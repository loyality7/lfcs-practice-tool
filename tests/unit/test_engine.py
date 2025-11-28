"""
Unit tests for the Engine class
Tests session orchestration, error handling, and data persistence
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime

from src.core.engine import Engine, SessionResult
from src.core.models import (
    Scenario, ValidationRules, CommandCheck, FileCheck, 
    ServiceCheck, CustomCheck
)
from src.utils.config import Config, DockerConfig, ScoringConfig
from src.validation.validator import ValidationResult, CheckResult
from src.utils.db_manager import Scorer


# Strategies for property-based testing

def scenario_strategy():
    """Generate valid scenarios for testing"""
    return st.builds(
        Scenario,
        id=st.text(min_size=5, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
        )),
        category=st.sampled_from(['networking', 'storage', 'users_groups', 
                                  'operations_deployment', 'essential_commands']),
        difficulty=st.sampled_from(['easy', 'medium', 'hard']),
        distribution=st.one_of(st.none(), st.sampled_from(['ubuntu', 'centos', 'rocky'])),
        task=st.text(min_size=10, max_size=200),
        setup_commands=st.lists(st.text(min_size=1, max_size=50), max_size=3),
        validation=st.builds(
            ValidationRules,
            checks=st.lists(
                st.builds(
                    CommandCheck,
                    command=st.text(min_size=1, max_size=50),
                    expected_exit_code=st.just(0),
                    expected_output=st.one_of(st.none(), st.text(max_size=50)),
                    regex_match=st.none(),
                    description=st.one_of(st.none(), st.text(max_size=50))
                ),
                min_size=1,
                max_size=5
            )
        ),
        points=st.integers(min_value=10, max_value=100),
        hints=st.lists(st.text(min_size=5, max_size=100), max_size=3),
        time_limit=st.one_of(st.none(), st.integers(min_value=60, max_value=3600))
    )


def validation_result_strategy():
    """Generate validation results"""
    checks_total = st.integers(min_value=1, max_value=10)
    
    @st.composite
    def _validation_result(draw):
        total = draw(checks_total)
        passed_count = draw(st.integers(min_value=0, max_value=total))
        
        check_results = []
        for i in range(total):
            check_results.append(CheckResult(
                check_name=f"Check {i+1}",
                passed=(i < passed_count),
                message="Check passed" if i < passed_count else "Check failed"
            ))
        
        return ValidationResult(
            passed=(passed_count == total),
            checks_passed=passed_count,
            checks_total=total,
            check_results=check_results,
            feedback=f"{passed_count}/{total} checks passed"
        )
    
    return _validation_result()


class TestEngine:
    """Test suite for Engine class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration"""
        config = Config()
        config.database_path = os.path.join(temp_dir, "test.db")
        config.logs_path = os.path.join(temp_dir, "logs")
        config.scenarios_path = os.path.join(temp_dir, "scenarios")
        
        # Create directories
        os.makedirs(config.logs_path, exist_ok=True)
        os.makedirs(config.scenarios_path, exist_ok=True)
        
        # Create a sample scenario file
        os.makedirs(os.path.join(config.scenarios_path, "storage", "easy"), exist_ok=True)
        scenario_file = os.path.join(config.scenarios_path, "storage", "easy", "test.yaml")
        with open(scenario_file, 'w') as f:
            f.write("""
id: test-scenario-01
category: storage
difficulty: easy
task: Create a test directory
validation:
  checks:
    - type: command
      command: "test -d /tmp/test"
      expected_exit_code: 0
points: 10
""")
        
        return config
    
    @pytest.fixture
    def mock_docker_manager(self):
        """Create mock Docker manager"""
        mock = Mock()
        mock.create_container = Mock(return_value=Mock(short_id="abc123", name="test-container"))
        mock.execute_command = Mock()
        mock.destroy_container = Mock()
        mock.get_container_shell = Mock(return_value="docker exec -it test-container /bin/bash")
        return mock
    
    @pytest.fixture
    def mock_validator(self):
        """Create mock validator"""
        mock = Mock()
        mock.validate = Mock(return_value=ValidationResult(
            passed=True,
            checks_passed=1,
            checks_total=1,
            check_results=[CheckResult(
                check_name="Test check",
                passed=True,
                message="Check passed"
            )],
            feedback="All checks passed"
        ))
        return mock
    
    def test_engine_initialization(self, test_config):
        """Test that engine initializes correctly"""
        with patch('src.core.engine.DockerManager') as mock_docker:
            mock_docker.return_value = Mock()
            
            engine = Engine(test_config)
            
            assert engine.config == test_config
            assert engine.scenario_loader is not None
            assert engine.docker_manager is not None
            assert engine.validator is not None
            assert engine.scorer is not None
            assert engine.current_session_id is None
            assert engine.current_container is None
    
    def test_get_statistics(self, test_config):
        """Test retrieving statistics"""
        with patch('src.core.engine.DockerManager') as mock_docker:
            mock_docker.return_value = Mock()
            
            engine = Engine(test_config)
            
            # Record some attempts
            engine.scorer.record_attempt(
                scenario_id="test-01",
                category="storage",
                difficulty="easy",
                score=10,
                max_score=10,
                passed=True,
                duration=60
            )
            
            stats = engine.get_statistics()
            
            assert stats.total_attempts == 1
            assert stats.total_passed == 1
            assert stats.total_score == 10
    
    def test_list_scenarios(self, test_config):
        """Test listing scenarios"""
        with patch('src.core.engine.DockerManager') as mock_docker:
            mock_docker.return_value = Mock()
            
            engine = Engine(test_config)
            
            scenarios = engine.list_scenarios()
            
            assert len(scenarios) >= 1
            assert all(isinstance(s, Scenario) for s in scenarios)
    
    def test_list_scenarios_with_filters(self, test_config):
        """Test listing scenarios with category and difficulty filters"""
        with patch('src.core.engine.DockerManager') as mock_docker:
            mock_docker.return_value = Mock()
            
            engine = Engine(test_config)
            
            scenarios = engine.list_scenarios(category="storage", difficulty="easy")
            
            assert all(s.category == "storage" for s in scenarios)
            assert all(s.difficulty == "easy" for s in scenarios)


class TestErrorRecovery:
    """Test suite for error recovery and data persistence"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration"""
        config = Config()
        config.database_path = os.path.join(temp_dir, "test.db")
        config.logs_path = os.path.join(temp_dir, "logs")
        config.scenarios_path = os.path.join(temp_dir, "scenarios")
        
        os.makedirs(config.logs_path, exist_ok=True)
        os.makedirs(config.scenarios_path, exist_ok=True)
        
        return config
    
    # Feature: lfcs-practice-environment, Property 13: Error recovery without data loss
    @given(
        error_stage=st.sampled_from(['container_creation', 'validation']),
        seed=st.integers(min_value=0, max_value=1000000)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_error_recovery_without_data_loss(self, error_stage, seed):
        """
        **Validates: Requirements 11.3, 11.4**
        
        Property: For any error condition (container failure, validation error),
        the system should handle it gracefully without losing previously recorded progress data.
        
        Test approach:
        1. Record some initial attempts in the database
        2. Simulate an error at different stages of session execution
        3. Verify that previously recorded data is still intact
        """
        # Create a fresh temp directory for this test run
        temp_dir = tempfile.mkdtemp(suffix=f"_{seed}")
        
        try:
            # Create a fresh config for this test
            config = Config()
            db_path = os.path.join(temp_dir, f"test_{error_stage}_{seed}.db")
            config.database_path = db_path
            config.logs_path = os.path.join(temp_dir, "logs")
            config.scenarios_path = os.path.join(temp_dir, "scenarios")
            
            os.makedirs(config.logs_path, exist_ok=True)
            os.makedirs(config.scenarios_path, exist_ok=True)
            
            # Create a simple valid scenario file
            os.makedirs(os.path.join(config.scenarios_path, "storage", "easy"), exist_ok=True)
            scenario_file = os.path.join(config.scenarios_path, "storage", "easy", "test.yaml")
            
            with open(scenario_file, 'w', encoding='utf-8') as f:
                f.write("""id: test-scenario-01
category: storage
difficulty: easy
task: Create a test directory
validation:
  checks:
    - type: command
      command: "echo test"
      expected_exit_code: 0
points: 10
""")
            
            # Step 1: Record initial attempts
            scorer = Scorer(config.database_path)
            
            initial_attempts = []
            for i in range(3):
                attempt_id = scorer.record_attempt(
                    scenario_id=f"initial-{seed}-{i}",
                    category="storage",
                    difficulty="easy",
                    score=10 * (i + 1),
                    max_score=100,
                    passed=True,
                    duration=60
                )
                initial_attempts.append(attempt_id)
            
            # Verify initial data is recorded
            initial_stats = scorer.get_statistics()
            assert initial_stats.total_attempts == 3
            assert initial_stats.total_passed == 3
            initial_total_score = initial_stats.total_score
            
            # Step 2: Simulate error during session
            with patch('src.core.engine.DockerManager') as mock_docker_class:
                mock_docker = Mock()
                mock_container = Mock(short_id="test123", name="test-container")
                
                if error_stage == 'container_creation':
                    # Simulate container creation failure
                    mock_docker.create_container = Mock(side_effect=Exception("Container creation failed"))
                elif error_stage == 'validation':
                    # Container creation succeeds, but validation fails
                    mock_docker.create_container = Mock(return_value=mock_container)
                    mock_docker.get_container_shell = Mock(return_value="docker exec -it test /bin/bash")
                    mock_docker.destroy_container = Mock()
                
                mock_docker_class.return_value = mock_docker
                
                # Create engine
                engine = Engine(config)
                
                # Replace validator with mock if needed
                if error_stage == 'validation':
                    engine.validator.validate = Mock(side_effect=Exception("Validation failed"))
                
                # Mock user input
                with patch('builtins.input', return_value=''):
                    with patch('builtins.print'):
                        # Attempt to start session (should fail)
                        try:
                            result = engine.start_session(
                                category="storage",
                                difficulty="easy"
                            )
                            # Should not reach here
                            assert False, f"Session should have failed for error_stage={error_stage}"
                            
                        except Exception as e:
                            # Error occurred as expected
                            pass
            
            # Step 3: Verify previously recorded data is still intact
            # Create a new scorer instance to ensure we're reading from disk
            new_scorer = Scorer(config.database_path)
            final_stats = new_scorer.get_statistics()
            
            # Check that initial data is preserved
            assert final_stats.total_attempts >= 3, \
                f"Data loss detected: expected at least 3 attempts, got {final_stats.total_attempts}"
            
            # Verify initial attempts are still there
            all_attempts = new_scorer.get_all_attempts()
            initial_attempt_ids = [a.scenario_id for a in all_attempts if a.scenario_id.startswith(f'initial-{seed}-')]
            assert len(initial_attempt_ids) == 3, \
                f"Initial attempts lost: expected 3, found {len(initial_attempt_ids)}"
            
            # Verify scores are preserved
            initial_attempts_data = [a for a in all_attempts if a.scenario_id.startswith(f'initial-{seed}-')]
            preserved_score = sum(a.score for a in initial_attempts_data)
            assert preserved_score == initial_total_score, \
                f"Score data corrupted: expected {initial_total_score}, got {preserved_score}"
        
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
