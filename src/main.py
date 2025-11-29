#!/usr/bin/env python3
"""
LFCS Practice Tool - Main Entry Point
AI-Powered Linux System Administration Practice Environment

This is the main entry point for the LFCS Practice Tool CLI application.
It handles:
- Configuration loading
- Logging setup
- Engine initialization
- CLI execution
- Top-level error handling
- Graceful shutdown
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Import from submodules using relative imports
from .cli.main_cli import CLI
from .core.engine import Engine
from .utils.config import load_config
from .utils.init import initialize_workspace


def setup_logging(logs_path: str, log_level: str = "INFO", console_output: bool = True) -> None:
    """
    Configure logging for the application
    
    Sets up both file and console logging with appropriate formatting.
    Creates log directory if it doesn't exist.
    
    Args:
        logs_path: Directory path for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output logs to console (stderr)
    """
    # Create logs directory if it doesn't exist
    Path(logs_path).mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with current date
    log_filename = f"lfcs-practice-{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join(logs_path, log_filename)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Build handlers list
    handlers = [
        # File handler - logs everything
        logging.FileHandler(log_filepath, encoding='utf-8')
    ]
    
    # Only add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info(f"LFCS Practice Tool - Session started")
    logger.info(f"Log file: {log_filepath}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Console output: {console_output}")
    logger.info("=" * 70)


def main():
    """
    Main entry point for the LFCS Practice Tool CLI application
    
    Workflow:
    1. Load configuration from files and environment variables
    2. Set up logging
    3. Check if command needs Docker (skip for help, list, stats)
    4. Check system prerequisites if needed
    5. Initialize the core engine
    6. Create and run the CLI
    7. Handle any errors gracefully
    8. Ensure proper cleanup on exit
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    logger = None
    engine = None
    
    try:
        # Step 1: Check if command needs Docker FIRST (before any initialization)
        # Commands like --help, --version don't need Docker
        needs_docker = True
        if len(sys.argv) <= 1:
            # No arguments - will show help, no Docker needed
            needs_docker = False
        elif any(arg in sys.argv for arg in ['--help', '-h', '--version']):
            # Help or version command - no Docker needed
            needs_docker = False
        # Note: list and stats DO need engine (for database/scenarios), so needs_docker stays True
        
        # Step 2: Initialize workspace and load configuration
        # Ensure data files exist in current directory
        initialize_workspace(os.getcwd())
        
        # This loads from config files and environment variables
        config = load_config()
        
        # Step 3: Set up logging
        # Must be done after config is loaded to get log path and level
        # Disable console logging for help/version commands to keep output clean
        setup_logging(config.logs_path, config.log_level, console_output=needs_docker)
        logger = logging.getLogger(__name__)
        
        logger.info("Configuration loaded successfully")
        logger.debug(f"Scenarios path: {config.scenarios_path}")
        logger.debug(f"Database path: {config.database_path}")
        logger.debug(f"AI enabled: {config.ai_enabled}")
        
        # Step 4: Check system prerequisites if Docker is needed
        if needs_docker:
            from .utils.system_check import check_prerequisites
            
            # Check if user wants to skip prerequisite check (via environment variable)
            skip_check = os.environ.get('SKIP_PREREQ_CHECK', '').lower() in ('true', '1', 'yes')
            
            if not skip_check:
                prereqs_ok = check_prerequisites(auto_fix=True)
                if not prereqs_ok:
                    print("\n⚠ Prerequisites check failed.")
                    print("You can still use 'lfcs list' and 'lfcs stats' commands.")
                    print("To skip this check (not recommended), set: export SKIP_PREREQ_CHECK=true\n")
                    return 10  # Exit code for missing prerequisites
        
        # Step 5: Initialize the core engine
        # This initializes all components (scenario loader, docker manager, etc.)
        logger.info("Initializing engine...")
        
        # Try to initialize engine, but allow CLI to work even if Docker fails
        try:
            engine = Engine(config)
            logger.info("Engine initialized successfully")
        except Exception as engine_error:
            if needs_docker:
                # If Docker is needed and engine fails, this is a real error
                raise
            else:
                # If Docker is not needed, create a minimal engine or skip it
                logger.warning(f"Engine initialization failed (Docker not available): {engine_error}")
                logger.info("Continuing without engine for non-Docker commands")
                engine = None
        
        # Step 6: Create and run the CLI
        logger.info("Starting CLI...")
        
        # Create CLI with engine (might be None for help commands)
        if engine is None and needs_docker:
            # This shouldn't happen, but handle it gracefully
            print("Error: Engine initialization failed. Cannot proceed.")
            return 1
        
        cli = CLI(engine) if engine else None
        
        # Handle commands that don't need engine
        if cli is None:
            # Show help or handle simple commands
            if '--version' in sys.argv:
                print(f"LFCS Practice Tool v{config.version}")
                return 0
            elif '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) <= 1:
                # Show full help even without engine
                from .utils import banner
                
                banner.print_usage_help()
                return 0
            else:
                # Show basic help
                print("LFCS Practice Tool - Interactive Linux System Administration Training")
                print("\nEngine initialization failed. Docker may not be available.")
                print("\nAvailable commands:")
                print("  lfcs --help     Show detailed help")
                print("  lfcs --version  Show version")
                print("\nTo use practice features, ensure Docker is installed and running.")
                return 0
        
        exit_code = cli.run()
        logger.info(f"CLI execution completed with exit code: {exit_code}")
        
        # Step 6: Graceful shutdown
        if engine:
            logger.info("Shutting down engine...")
            engine.shutdown()
            logger.info("Engine shutdown complete")
        
        logger.info("LFCS Practice Tool - Session ended")
        logger.info("=" * 70)
        
        return exit_code
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\nInterrupted by user")
        if logger:
            logger.info("Application interrupted by user (Ctrl+C)")
        
        # Attempt cleanup
        if engine:
            try:
                engine.shutdown()
            except Exception as cleanup_error:
                if logger:
                    logger.error(f"Error during interrupt cleanup: {cleanup_error}")
        
        return 130  # Standard exit code for SIGINT
        
    except FileNotFoundError as e:
        # Handle missing files (config, scenarios, etc.)
        error_msg = f"Required file or directory not found: {e}"
        print(f"Error: {error_msg}")
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            # If logging isn't set up yet, print to stderr
            print(f"Details: {e}", file=sys.stderr)
        
        return 2
        
    except PermissionError as e:
        # Handle permission issues (database, logs, etc.)
        error_msg = f"Permission denied: {e}"
        print(f"Error: {error_msg}")
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            print(f"Details: {e}", file=sys.stderr)
        
        print("\nTry running with appropriate permissions or check file/directory ownership.")
        return 3
        
    except ValueError as e:
        # Handle configuration errors
        error_msg = f"Configuration error: {e}"
        print(f"Error: {error_msg}")
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            print(f"Details: {e}", file=sys.stderr)
        
        print("\nCheck your configuration files in the config/ directory.")
        return 4
        
    except ImportError as e:
        # Handle missing dependencies
        error_msg = f"Missing dependency: {e}"
        print(f"Error: {error_msg}")
        if logger:
            logger.error(error_msg, exc_info=True)
        else:
            print(f"Details: {e}", file=sys.stderr)
        
        print("\nTry running: pip install -r requirements.txt")
        return 5
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error: {e}"
        print(f"Fatal error: {error_msg}")
        
        if logger:
            logger.critical(error_msg, exc_info=True)
        else:
            # If logging isn't set up, print full traceback
            import traceback
            traceback.print_exc(file=sys.stderr)
        
        # Attempt cleanup even on fatal error
        if engine:
            try:
                engine.shutdown()
            except Exception as cleanup_error:
                if logger:
                    logger.error(f"Error during fatal error cleanup: {cleanup_error}")
        
        return 1
    
    finally:
        # Ensure any remaining cleanup happens
        # This runs regardless of how we exit
        if logger:
            logger.debug("Main function cleanup complete")


if __name__ == "__main__":
    # Execute main and exit with its return code
    exit_code = main()
    sys.exit(exit_code)
