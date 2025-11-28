"""
Core Engine for LFCS Practice Tool
Orchestrates practice sessions, coordinates components, and manages workflow
"""

import logging
import time
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import tempfile
import threading
import shutil
import os

from .scenario_loader import ScenarioLoader
from .models import Scenario
from ..docker_manager.container import DockerManager
from ..docker_manager.environment import DockerEnvironment
from ..validation.validator import Validator
from ..core.models import ValidationResult
from ..utils.db_manager import Scorer, Statistics
from ..utils.config import Config
from ..utils.error_handler import ErrorHandler, ErrorContext


logger = logging.getLogger(__name__)


@dataclass
class SessionResult:
    """Result of a practice session"""
    scenario: Scenario
    validation_result: ValidationResult
    score: int
    duration: int  # seconds
    passed: bool
    container_id: Optional[str] = None


class Engine:
    """
    Core orchestration engine for LFCS Practice Tool
    
    Responsibilities:
    - Initialize and coordinate all system components
    - Manage practice session lifecycle
    - Handle errors and recovery
    - Provide statistics and scenario listing
    """
    
    def __init__(self, config: Config):
        """
        Initialize engine with configuration
        
        Args:
            config: System configuration
        """
        self.config = config
        self.error_handler = ErrorHandler(config.logs_path)
        
        # Initialize logging
        self._setup_logging()
        
        logger.info("Initializing LFCS Practice Engine")
        
        try:
            # Initialize components
            self.scenario_loader = ScenarioLoader(config.scenarios_path)
            self.docker_manager = DockerManager(config.docker_config)
            self.validator = Validator()
            self.scorer = Scorer(config.database_path)
            
            # Load scenarios
            logger.info("Loading scenarios...")
            self.scenario_loader.load_all()
            scenario_count = self.scenario_loader.get_scenario_count()
            logger.info(f"Loaded {scenario_count} scenarios")
            
            # Session state
            self.current_session_id: Optional[str] = None
            self.current_container = None
            
            logger.info("Engine initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            
            # Use error handler for better error reporting
            context = ErrorContext(user_action="initialize_engine")
            response = self.error_handler.handle_error(e, context)
            print(self.error_handler.format_error_for_user(response))
            
            raise
    
    def start_session(self, category: Optional[str] = None, 
                     difficulty: Optional[str] = None,
                     distribution: Optional[str] = None,
                     ai_mode: bool = False,
                     scenario_id: Optional[str] = None) -> SessionResult:
        """
        Start and manage a complete practice session
        
        Workflow:
        1. Load or generate scenario
        2. Create Docker container
        3. Display task to user
        4. Wait for user to complete task
        5. Run validation
        6. Calculate score
        7. Persist results
        8. Clean up container
        9. Return results
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            distribution: Optional distribution (defaults to config default)
            ai_mode: Whether to use AI features (not implemented yet)
            scenario_id: Optional specific scenario ID to run
        
        Returns:
            SessionResult with all session details
        
        Raises:
            ValueError: If no scenarios match criteria
            Exception: For other errors during session
        """
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        start_time = time.time()
        
        logger.info(f"Starting session {session_id}")
        logger.info(f"Filters - Category: {category}, Difficulty: {difficulty}, Distribution: {distribution}, Scenario ID: {scenario_id}")
        
        try:
            # Step 1: Load scenario
            logger.info("Step 1: Loading scenario")
            scenario = self._load_scenario(category, difficulty, distribution, scenario_id)
            
            if not scenario:
                raise ValueError(
                    f"No scenarios found matching criteria: "
                    f"category={category}, difficulty={difficulty}, distribution={distribution}"
                )
            
            logger.info(f"Selected scenario: {scenario.id} - {scenario.task}")
            
            # Step 2: Create container
            logger.info("Step 2: Creating Docker container")
            
            # Create control directory for live validation
            control_dir = tempfile.mkdtemp(prefix="lfcs-control-")
            os.chmod(control_dir, 0o777)  # Ensure container can write to it
            self.config.docker_config.control_dir = control_dir
            
            dist = distribution or self.config.docker_config.default_distribution
            container = self._create_container(dist, scenario)
            self.current_container = container
            
            # Inject validation agent
            self._inject_agent(container)
            
            logger.info(f"Container created: {container.short_id}")
            
            # Start validation monitor
            stop_monitor = threading.Event()
            monitor_thread = threading.Thread(
                target=self._monitor_validation_requests,
                args=(control_dir, container, scenario, stop_monitor),
                daemon=True
            )
            monitor_thread.start()
            
            # Step 3: Display task to user
            logger.info("Step 3: Presenting task to user")
            self._display_task(scenario, container)
            
            # Step 4: Wait for user to complete task
            logger.info("Step 4: Waiting for user to complete task")
            self._wait_for_user()
            
            # Step 5: Run validation
            logger.info("Step 5: Running validation")
            validation_result = self._validate_scenario(container, scenario)
            
            # Step 6: Calculate score
            logger.info("Step 6: Calculating score")
            score = self._calculate_score(scenario, validation_result)
            
            # Step 7: Persist results
            logger.info("Step 7: Persisting results to database")
            duration = int(time.time() - start_time)
            self._record_attempt(scenario, score, validation_result.passed, duration)
            
            # Step 8: Clean up
            logger.info("Step 8: Cleaning up")
            stop_monitor.set()
            monitor_thread.join(timeout=1.0)
            shutil.rmtree(control_dir, ignore_errors=True)
            
            self._cleanup_container(container)
            self.current_container = None
            
            # Step 9: Return results
            session_result = SessionResult(
                scenario=scenario,
                validation_result=validation_result,
                score=score,
                duration=duration,
                passed=validation_result.passed,
                container_id=container.short_id
            )
            
            logger.info(f"Session {session_id} complete - Passed: {validation_result.passed}, Score: {score}")
            self.current_session_id = None
            
            return session_result
            
        except Exception as e:
            logger.error(f"Session {session_id} failed: {e}")
            
            # Use error handler for better error reporting
            context = ErrorContext(
                scenario_id=scenario.id if 'scenario' in locals() else None,
                container_id=self.current_container.short_id if self.current_container else None,
                user_action="start_session",
                category=category,
                difficulty=difficulty,
                additional_info={'session_id': session_id}
            )
            response = self.error_handler.handle_error(e, context)
            print(self.error_handler.format_error_for_user(response))
            
            # Attempt cleanup on error
            if self.current_container:
                try:
                    logger.info("Attempting cleanup after error")
                    self._cleanup_container(self.current_container)
                    self.current_container = None
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")
                    cleanup_context = ErrorContext(
                        container_id=self.current_container.short_id if self.current_container else None,
                        user_action="cleanup_after_error"
                    )
                    cleanup_response = self.error_handler.handle_error(cleanup_error, cleanup_context)
                    logger.error(f"Cleanup error: {cleanup_response.message}")
            
            self.current_session_id = None
            
            # Re-raise if it's a critical error
            if response.should_exit:
                raise
            else:
                raise
    
    def get_statistics(self, category: Optional[str] = None) -> Statistics:
        """
        Retrieve user statistics
        
        Args:
            category: Optional category filter
        
        Returns:
            Statistics object with performance data
        """
        logger.info(f"Retrieving statistics (category={category})")
        
        try:
            stats = self.scorer.get_statistics(category)
            logger.info(f"Statistics retrieved: {stats.total_attempts} attempts, {stats.total_passed} passed")
            return stats
        except Exception as e:
            logger.error(f"Failed to retrieve statistics: {e}")
            raise
    
    def list_scenarios(self, category: Optional[str] = None,
                      difficulty: Optional[str] = None) -> List[Scenario]:
        """
        List available scenarios
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
        
        Returns:
            List of matching scenarios
        """
        logger.info(f"Listing scenarios (category={category}, difficulty={difficulty})")
        
        try:
            scenarios = self.scenario_loader.list_scenarios(category, difficulty)
            logger.info(f"Found {len(scenarios)} matching scenarios")
            return scenarios
        except Exception as e:
            logger.error(f"Failed to list scenarios: {e}")
            raise
    
    def get_recommendations(self) -> List[str]:
        """
        Get personalized recommendations based on user performance
        
        Returns:
            List of recommendation strings
        """
        logger.info("Generating recommendations")
        
        try:
            stats = self.scorer.get_statistics()
            recommendations = self.scorer.get_recommendations(stats)
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            raise
    
    def _load_scenario(self, category: Optional[str], difficulty: Optional[str],
                      distribution: Optional[str], scenario_id: Optional[str] = None) -> Optional[Scenario]:
        """Load a scenario matching criteria or by specific ID"""
        try:
            if scenario_id:
                # Load specific scenario by ID
                scenario = self.scenario_loader.get_by_id(scenario_id)
            else:
                # Load random scenario matching filters
                scenario = self.scenario_loader.get_scenario(category, difficulty, distribution)
            return scenario
        except Exception as e:
            logger.error(f"Failed to load scenario: {e}")
            raise
    
    def _create_container(self, distribution: str, scenario: Scenario):
        """Create and configure container"""
        try:
            container = self.docker_manager.create_container(distribution, scenario)
            return container
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    def _display_task(self, scenario: Scenario, container):
        """Display task information to user"""
        from ..utils.colors import Colors, header, info, dim, highlight, success, warning, error
        
        print("\n" + Colors.CYAN + "=" * 70 + Colors.RESET)
        print(header(f"SCENARIO: {scenario.id}"))
        print(Colors.CYAN + "=" * 70 + Colors.RESET)
        
        print(f"\n{highlight('Category:')} {info(scenario.category)}")
        print(f"{highlight('Difficulty:')} {info(scenario.difficulty.capitalize())}")
        print(f"{highlight('Points:')} {info(str(scenario.points))}")
        
        print(f"\n{highlight('TASK:')}")
        print(f"{scenario.task}\n")
        
        if scenario.hints:
            print(f"{highlight('HINTS:')}")
            for i, hint in enumerate(scenario.hints, 1):
                print(f"  {dim(f'{i}.')} {hint}")
            print()
        
        if scenario.time_limit:
            print(f"{highlight('TIME LIMIT:')} {warning(f'{scenario.time_limit} seconds')}\n")
        
        print(Colors.CYAN + "=" * 70 + Colors.RESET)
        print(f"\n{success('✓')} Container ready: {info(container.short_id)}")
        print(f"{dim('Opening Docker shell...')}\n")
        print(Colors.CYAN + "=" * 70 + Colors.RESET + "\n")
    
    def _wait_for_user(self):
        """Open Docker shell and wait for user to complete the task"""
        import subprocess
        import os
        
        # Get the shell command
        shell_cmd = self.docker_manager.get_container_shell(self.current_container)
        
        # Display instructions
        from ..utils.colors import Colors, info, dim, warning, success
        print(f"{info('📝 Instructions:')}")
        print(f"  • Complete the task in the Docker shell that will open")
        print(f"  • Type {warning('exit')} when you're done to return and validate")
        print(f"  • Your work will be automatically validated\n")
        
        print(dim("Press Enter to open the Docker shell..."))
        input()
        
        try:
            # Open interactive shell
            print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
            print(f"{success('Opening Docker shell...')}")
            print(f"{dim('Type')} {warning('exit')} {dim('when finished')}")
            print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")
            
            # Run docker exec interactively
            subprocess.run(shell_cmd, shell=True)
            
            print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
            print(f"{success('✓')} Shell closed. Starting validation...")
            print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")
            
        except Exception as e:
            logger.error(f"Failed to open shell: {e}")
            print(f"\n{warning('⚠')} Could not open shell automatically.")
            print(f"{dim('You can manually access the container with:')}")
            print(f"  {shell_cmd}\n")
            print(f"{dim('Press Enter when ready for validation...')}")
            input()
    
    def _validate_scenario(self, container, scenario: Scenario) -> ValidationResult:
        """Run validation checks"""
        try:
            # Wrap container in environment adapter
            environment = DockerEnvironment(container)
            validation_result = self.validator.validate(environment, scenario)
            
            # Display feedback
            print(validation_result.feedback)
            
            return validation_result
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def _calculate_score(self, scenario: Scenario, validation_result: ValidationResult) -> int:
        """Calculate score based on validation results"""
        try:
            score = self.scorer.calculate_score(
                max_score=scenario.points,
                checks_passed=validation_result.checks_passed,
                checks_total=validation_result.checks_total,
                difficulty=scenario.difficulty,
                difficulty_multipliers=self.config.scoring_config.difficulty_multipliers
            )
            return score
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            raise
    
    def _record_attempt(self, scenario: Scenario, score: int, passed: bool, duration: int):
        """Record attempt in database"""
        try:
            self.scorer.record_attempt(
                scenario_id=scenario.id,
                category=scenario.category,
                difficulty=scenario.difficulty,
                score=score,
                max_score=scenario.points,
                passed=passed,
                duration=duration
            )
        except Exception as e:
            logger.error(f"Failed to record attempt: {e}")
            # Don't raise - we don't want to fail the session if recording fails
    
    def _cleanup_container(self, container):
        """Clean up container resources"""
        try:
            if self.config.docker_config.cleanup_on_exit:
                self.docker_manager.destroy_container(container)
                logger.info("Container cleaned up successfully")
            else:
                logger.info("Container cleanup skipped (cleanup_on_exit=False)")
        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
            # Don't raise - cleanup failure shouldn't fail the session
    
    def _setup_logging(self):
        """Configure logging"""
        # Create logs directory if it doesn't exist
        import os
        os.makedirs(self.config.logs_path, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(
            self.config.logs_path,
            f"lfcs-practice-{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _inject_agent(self, container):
        """Inject validation agent into container"""
        try:
            # Get the package root directory
            package_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            agent_src = os.path.join(package_root, 'src', 'agent', 'lfcs-check')
            
            if os.path.exists(agent_src):
                self.docker_manager.copy_to_container(container, agent_src, '/usr/local/bin/')
                self.docker_manager.execute_command(container, 'chmod +x /usr/local/bin/lfcs-check')
                logger.info("Validation agent injected")
            else:
                logger.warning(f"Validation agent not found at {agent_src}")
        except Exception as e:
            logger.error(f"Failed to inject agent: {e}")

    def _monitor_validation_requests(self, control_dir: str, container, scenario: Scenario, stop_event: threading.Event):
        """Monitor control directory for validation requests"""
        request_file = os.path.join(control_dir, "request")
        response_file = os.path.join(control_dir, "response")
        
        logger.info("Started validation monitor")
        
        while not stop_event.is_set():
            if os.path.exists(request_file):
                try:
                    logger.info("Received validation request")
                    # Give file system a moment to sync
                    time.sleep(0.1)
                    try:
                        os.remove(request_file)
                    except FileNotFoundError:
                        continue
                    
                    # Run validation
                    result = self._validate_scenario(container, scenario)
                    
                    # Write response
                    with open(response_file, 'w') as f:
                        f.write(result.feedback)
                    
                    # Ensure permissions so container can read/delete
                    os.chmod(response_file, 0o666)
                        
                except Exception as e:
                    logger.error(f"Error processing validation request: {e}")
                    
            time.sleep(0.5)

    def shutdown(self):
        """Gracefully shutdown the engine"""
        logger.info("Shutting down engine")
        
        # Clean up any active container
        if self.current_container:
            try:
                logger.info("Cleaning up active container")
                self._cleanup_container(self.current_container)
                self.current_container = None
            except Exception as e:
                logger.error(f"Error during shutdown cleanup: {e}")
        
        logger.info("Engine shutdown complete")
