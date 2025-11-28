"""
Comprehensive Error Handler for LFCS Practice Tool
Provides centralized error handling, logging, and recovery suggestions
"""

import logging
import traceback
import sys
import os
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import docker
from docker.errors import DockerException, ImageNotFound, APIError, NotFound
import sqlite3
import yaml


logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur"""
    DOCKER = "docker"
    SCENARIO = "scenario"
    VALIDATION = "validation"
    DATABASE = "database"
    AI = "ai"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    CRITICAL = "critical"  # System cannot continue
    ERROR = "error"        # Operation failed but system can continue
    WARNING = "warning"    # Potential issue but operation succeeded
    INFO = "info"          # Informational message


@dataclass
class ErrorContext:
    """Context information for an error"""
    scenario_id: Optional[str] = None
    container_id: Optional[str] = None
    user_action: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class ErrorResponse:
    """Response from error handling"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    recovery_suggestions: List[str]
    should_retry: bool
    should_exit: bool
    context: ErrorContext


class ErrorHandler:
    """
    Centralized error handling for the LFCS Practice Tool
    
    Responsibilities:
    - Categorize and classify errors
    - Provide user-friendly error messages
    - Suggest recovery actions
    - Log errors with full context
    - Determine if operations should retry or exit
    """
    
    def __init__(self, log_path: str = "logs"):
        """
        Initialize error handler
        
        Args:
            log_path: Path to logs directory
        """
        self.log_path = log_path
        self._ensure_log_directory()
    
    def handle_error(self, error: Exception, context: ErrorContext) -> ErrorResponse:
        """
        Central error handling with context
        
        Args:
            error: The exception that occurred
            context: Context information about where/when error occurred
            
        Returns:
            ErrorResponse with categorized error and recovery suggestions
        """
        # Categorize the error
        category = self._categorize_error(error)
        severity = self._determine_severity(error, category)
        
        # Generate messages
        message = str(error)
        user_message = self._generate_user_message(error, category, context)
        recovery_suggestions = self._suggest_recovery(error, category, context)
        
        # Determine retry/exit behavior
        should_retry = self._should_retry(error, category)
        should_exit = self._should_exit(error, category, severity)
        
        # Log the error
        self.log_error(error, context, category, severity)
        
        return ErrorResponse(
            category=category,
            severity=severity,
            message=message,
            user_message=user_message,
            recovery_suggestions=recovery_suggestions,
            should_retry=should_retry,
            should_exit=should_exit,
            context=context
        )
    
    def log_error(self, error: Exception, context: ErrorContext, 
                  category: ErrorCategory, severity: ErrorSeverity) -> None:
        """
        Log error with full context
        
        Args:
            error: The exception
            context: Error context
            category: Error category
            severity: Error severity
        """
        log_level = self._get_log_level(severity)
        
        # Build context string
        context_parts = []
        if context.scenario_id:
            context_parts.append(f"scenario={context.scenario_id}")
        if context.container_id:
            context_parts.append(f"container={context.container_id}")
        if context.user_action:
            context_parts.append(f"action={context.user_action}")
        if context.category:
            context_parts.append(f"category={context.category}")
        if context.difficulty:
            context_parts.append(f"difficulty={context.difficulty}")
        
        context_str = ", ".join(context_parts) if context_parts else "no context"
        
        # Log the error
        logger.log(
            log_level,
            f"[{category.value.upper()}] {type(error).__name__}: {str(error)} "
            f"({context_str})"
        )
        
        # Log stack trace for errors and critical issues
        if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            logger.log(log_level, f"Stack trace:\n{traceback.format_exc()}")
        
        # Log additional context if available
        if context.additional_info:
            logger.log(log_level, f"Additional info: {context.additional_info}")
        
        # Log system state for critical errors
        if severity == ErrorSeverity.CRITICAL:
            system_state = self._get_system_state()
            logger.log(log_level, f"System state: {system_state}")
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type"""
        # Docker errors
        if isinstance(error, (DockerException, ImageNotFound, APIError, NotFound)):
            return ErrorCategory.DOCKER
        
        # Database errors
        if isinstance(error, (sqlite3.Error, sqlite3.DatabaseError, 
                            sqlite3.IntegrityError, sqlite3.OperationalError)):
            return ErrorCategory.DATABASE
        
        # YAML/Scenario errors
        if isinstance(error, (yaml.YAMLError, yaml.scanner.ScannerError)):
            return ErrorCategory.SCENARIO
        
        # File system errors
        if isinstance(error, (FileNotFoundError, PermissionError, OSError)):
            return ErrorCategory.SYSTEM
        
        # Value errors often indicate validation issues
        if isinstance(error, ValueError):
            # Check error message for clues
            error_msg = str(error).lower()
            if 'scenario' in error_msg or 'yaml' in error_msg:
                return ErrorCategory.SCENARIO
            elif 'validation' in error_msg or 'check' in error_msg:
                return ErrorCategory.VALIDATION
            elif 'config' in error_msg:
                return ErrorCategory.CONFIGURATION
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, 
                           category: ErrorCategory) -> ErrorSeverity:
        """Determine severity of an error"""
        # Critical errors that prevent system operation
        if isinstance(error, DockerException) and "not running" in str(error).lower():
            return ErrorSeverity.CRITICAL
        
        if isinstance(error, sqlite3.DatabaseError) and "corrupt" in str(error).lower():
            return ErrorSeverity.CRITICAL
        
        if isinstance(error, PermissionError):
            return ErrorSeverity.CRITICAL
        
        # Errors that fail an operation but system can continue
        if category in [ErrorCategory.DOCKER, ErrorCategory.DATABASE, 
                       ErrorCategory.VALIDATION]:
            return ErrorSeverity.ERROR
        
        # Warnings for recoverable issues
        if isinstance(error, (FileNotFoundError, ValueError)):
            return ErrorSeverity.WARNING
        
        return ErrorSeverity.ERROR
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory,
                               context: ErrorContext) -> str:
        """Generate user-friendly error message"""
        if category == ErrorCategory.DOCKER:
            return self._generate_docker_message(error, context)
        elif category == ErrorCategory.SCENARIO:
            return self._generate_scenario_message(error, context)
        elif category == ErrorCategory.VALIDATION:
            return self._generate_validation_message(error, context)
        elif category == ErrorCategory.DATABASE:
            return self._generate_database_message(error, context)
        elif category == ErrorCategory.CONFIGURATION:
            return self._generate_configuration_message(error, context)
        elif category == ErrorCategory.SYSTEM:
            return self._generate_system_message(error, context)
        else:
            return f"An unexpected error occurred: {str(error)}"
    
    def _generate_docker_message(self, error: Exception, 
                                context: ErrorContext) -> str:
        """Generate user message for Docker errors"""
        error_msg = str(error).lower()
        
        if "not running" in error_msg or "cannot connect" in error_msg:
            return (
                "Docker daemon is not running or not accessible.\n"
                "The LFCS Practice Tool requires Docker to create isolated practice environments."
            )
        
        if isinstance(error, ImageNotFound):
            return (
                f"Docker image not found.\n"
                f"The required base image for this scenario is not available on your system."
            )
        
        if "permission denied" in error_msg:
            return (
                "Permission denied when accessing Docker.\n"
                "Your user account may not have permission to use Docker."
            )
        
        if "no space" in error_msg or "disk" in error_msg:
            return (
                "Insufficient disk space for Docker operation.\n"
                "Docker needs space to create and run containers."
            )
        
        if "timeout" in error_msg:
            return (
                "Docker operation timed out.\n"
                "The container may be taking too long to start or respond."
            )
        
        return f"Docker error: {str(error)}"
    
    def _generate_scenario_message(self, error: Exception,
                                   context: ErrorContext) -> str:
        """Generate user message for scenario errors"""
        error_msg = str(error)
        
        if isinstance(error, yaml.YAMLError):
            return (
                f"Failed to parse scenario YAML file.\n"
                f"There is a syntax error in the scenario definition.\n"
                f"Error: {error_msg}"
            )
        
        if "no scenarios found" in error_msg.lower():
            filters = []
            if context.category:
                filters.append(f"category={context.category}")
            if context.difficulty:
                filters.append(f"difficulty={context.difficulty}")
            
            filter_str = ", ".join(filters) if filters else "specified criteria"
            return (
                f"No scenarios found matching {filter_str}.\n"
                f"Try different filters or check that scenario files exist."
            )
        
        if "missing required field" in error_msg.lower():
            return (
                f"Scenario definition is incomplete.\n"
                f"{error_msg}"
            )
        
        return f"Scenario error: {error_msg}"
    
    def _generate_validation_message(self, error: Exception,
                                     context: ErrorContext) -> str:
        """Generate user message for validation errors"""
        error_msg = str(error)
        
        if "command execution failed" in error_msg.lower():
            return (
                f"Failed to execute validation command in container.\n"
                f"The container may not be responding or the command may be invalid.\n"
                f"Error: {error_msg}"
            )
        
        if "script not found" in error_msg.lower():
            return (
                f"Validation script not found.\n"
                f"The custom validation script specified in the scenario does not exist.\n"
                f"Error: {error_msg}"
            )
        
        if "timeout" in error_msg.lower():
            return (
                f"Validation check timed out.\n"
                f"The validation command took too long to complete."
            )
        
        return f"Validation error: {error_msg}"
    
    def _generate_database_message(self, error: Exception,
                                   context: ErrorContext) -> str:
        """Generate user message for database errors"""
        error_msg = str(error).lower()
        
        if "locked" in error_msg:
            return (
                "Database is locked by another process.\n"
                "Another instance of the tool may be running, or the database is being accessed."
            )
        
        if "corrupt" in error_msg or "malformed" in error_msg:
            return (
                "Database file is corrupted.\n"
                "Your progress database may be damaged and needs to be repaired or reset."
            )
        
        if "disk" in error_msg or "space" in error_msg:
            return (
                "Insufficient disk space for database operation.\n"
                "Free up some disk space and try again."
            )
        
        if "permission" in error_msg:
            return (
                "Permission denied when accessing database.\n"
                "Check that you have write permissions to the database directory."
            )
        
        return f"Database error: {str(error)}"
    
    def _generate_configuration_message(self, error: Exception,
                                       context: ErrorContext) -> str:
        """Generate user message for configuration errors"""
        return (
            f"Configuration error: {str(error)}\n"
            f"Check your configuration files in the config/ directory."
        )
    
    def _generate_system_message(self, error: Exception,
                                context: ErrorContext) -> str:
        """Generate user message for system errors"""
        if isinstance(error, FileNotFoundError):
            return (
                f"File not found: {str(error)}\n"
                f"A required file or directory is missing."
            )
        
        if isinstance(error, PermissionError):
            return (
                f"Permission denied: {str(error)}\n"
                f"You don't have permission to access this resource."
            )
        
        return f"System error: {str(error)}"
    
    def _suggest_recovery(self, error: Exception, category: ErrorCategory,
                         context: ErrorContext) -> List[str]:
        """Provide recovery suggestions based on error type"""
        suggestions = []
        
        if category == ErrorCategory.DOCKER:
            suggestions.extend(self._docker_recovery_suggestions(error))
        elif category == ErrorCategory.SCENARIO:
            suggestions.extend(self._scenario_recovery_suggestions(error, context))
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend(self._validation_recovery_suggestions(error))
        elif category == ErrorCategory.DATABASE:
            suggestions.extend(self._database_recovery_suggestions(error))
        elif category == ErrorCategory.CONFIGURATION:
            suggestions.extend(self._configuration_recovery_suggestions(error))
        elif category == ErrorCategory.SYSTEM:
            suggestions.extend(self._system_recovery_suggestions(error))
        
        return suggestions
    
    def _docker_recovery_suggestions(self, error: Exception) -> List[str]:
        """Recovery suggestions for Docker errors"""
        suggestions = []
        error_msg = str(error).lower()
        
        if "not running" in error_msg or "cannot connect" in error_msg:
            suggestions.extend([
                "Install Docker: https://docs.docker.com/get-docker/",
                "Start Docker daemon: sudo systemctl start docker (Linux) or start Docker Desktop (Mac/Windows)",
                "Check Docker status: docker ps",
                "Verify Docker installation: docker --version"
            ])
        
        elif isinstance(error, ImageNotFound):
            suggestions.extend([
                "Build base images: cd docker/base_images && ./build_all.sh",
                "Pull image manually: docker pull <image-name>",
                "Check available images: docker images"
            ])
        
        elif "permission denied" in error_msg:
            suggestions.extend([
                "Add your user to docker group: sudo usermod -aG docker $USER",
                "Log out and back in for group changes to take effect",
                "Run with sudo (not recommended for regular use)",
                "Check Docker socket permissions: ls -l /var/run/docker.sock"
            ])
        
        elif "no space" in error_msg or "disk" in error_msg:
            suggestions.extend([
                "Free up disk space",
                "Remove unused Docker images: docker image prune -a",
                "Remove unused containers: docker container prune",
                "Check disk usage: df -h"
            ])
        
        elif "timeout" in error_msg:
            suggestions.extend([
                "Wait a moment and try again",
                "Check Docker daemon logs: journalctl -u docker",
                "Restart Docker daemon",
                "Check system resources: top or htop"
            ])
        
        else:
            suggestions.extend([
                "Check Docker daemon logs: journalctl -u docker",
                "Restart Docker daemon",
                "Check Docker documentation: https://docs.docker.com/"
            ])
        
        return suggestions
    
    def _scenario_recovery_suggestions(self, error: Exception,
                                      context: ErrorContext) -> List[str]:
        """Recovery suggestions for scenario errors"""
        suggestions = []
        error_msg = str(error).lower()
        
        if "yaml" in error_msg or "parse" in error_msg:
            suggestions.extend([
                "Check YAML syntax in the scenario file",
                "Validate YAML online: https://www.yamllint.com/",
                "Ensure proper indentation (use spaces, not tabs)",
                "Check for missing colons or quotes"
            ])
        
        elif "no scenarios found" in error_msg:
            suggestions.extend([
                "List available scenarios: lfcs-practice list",
                "Try different category or difficulty filters",
                "Check that scenario files exist in scenarios/ directory",
                "Verify scenario files have .yaml extension"
            ])
        
        elif "missing required field" in error_msg:
            suggestions.extend([
                "Review scenario file structure",
                "Check design document for required fields",
                "Compare with example scenarios in scenarios/ directory"
            ])
        
        else:
            suggestions.extend([
                "Check scenario file syntax and structure",
                "Review example scenarios for correct format",
                "Check logs for detailed error information"
            ])
        
        return suggestions
    
    def _validation_recovery_suggestions(self, error: Exception) -> List[str]:
        """Recovery suggestions for validation errors"""
        suggestions = []
        error_msg = str(error).lower()
        
        if "command execution failed" in error_msg:
            suggestions.extend([
                "Check that the container is running: docker ps",
                "Verify the validation command syntax",
                "Check container logs: docker logs <container-id>",
                "Try accessing the container: docker exec -it <container-id> /bin/bash"
            ])
        
        elif "script not found" in error_msg:
            suggestions.extend([
                "Check that validation script exists in docker/validation_scripts/",
                "Verify script path in scenario definition",
                "Ensure script has execute permissions: chmod +x <script>",
                "Check that script was copied to container"
            ])
        
        elif "timeout" in error_msg:
            suggestions.extend([
                "Increase timeout value in configuration",
                "Check if command is hanging or waiting for input",
                "Verify container has sufficient resources",
                "Check container logs for issues"
            ])
        
        else:
            suggestions.extend([
                "Review validation rules in scenario",
                "Check container state and logs",
                "Try running validation commands manually in container"
            ])
        
        return suggestions
    
    def _database_recovery_suggestions(self, error: Exception) -> List[str]:
        """Recovery suggestions for database errors"""
        suggestions = []
        error_msg = str(error).lower()
        
        if "locked" in error_msg:
            suggestions.extend([
                "Wait a moment and try again",
                "Close other instances of the tool",
                "Check for processes using the database: lsof database/progress.db",
                "If persistent, restart your system"
            ])
        
        elif "corrupt" in error_msg or "malformed" in error_msg:
            suggestions.extend([
                "Backup current database: cp database/progress.db database/progress.db.backup",
                "Reset database: rm database/progress.db (WARNING: loses all progress)",
                "Try SQLite recovery tools",
                "Check disk for errors: fsck (Linux) or disk utility (Mac/Windows)"
            ])
        
        elif "disk" in error_msg or "space" in error_msg:
            suggestions.extend([
                "Free up disk space",
                "Check disk usage: df -h",
                "Remove unnecessary files",
                "Move database to location with more space"
            ])
        
        elif "permission" in error_msg:
            suggestions.extend([
                "Check database file permissions: ls -l database/progress.db",
                "Ensure database directory is writable",
                "Check parent directory permissions",
                "Run with appropriate user permissions"
            ])
        
        else:
            suggestions.extend([
                "Check database file integrity",
                "Review database logs",
                "Consider resetting database if issue persists"
            ])
        
        return suggestions
    
    def _configuration_recovery_suggestions(self, error: Exception) -> List[str]:
        """Recovery suggestions for configuration errors"""
        return [
            "Check configuration file syntax (YAML format)",
            "Review config/config.yaml for errors",
            "Compare with example configuration",
            "Check for missing required fields",
            "Verify file paths and values are correct",
            "Use environment variables to override if needed"
        ]
    
    def _system_recovery_suggestions(self, error: Exception) -> List[str]:
        """Recovery suggestions for system errors"""
        suggestions = []
        
        if isinstance(error, FileNotFoundError):
            suggestions.extend([
                "Check that all required files and directories exist",
                "Verify installation is complete",
                "Check file paths in configuration",
                "Reinstall if necessary"
            ])
        
        elif isinstance(error, PermissionError):
            suggestions.extend([
                "Check file and directory permissions",
                "Ensure you have necessary access rights",
                "Run with appropriate user permissions",
                "Check parent directory permissions"
            ])
        
        else:
            suggestions.extend([
                "Check system logs for more information",
                "Verify system requirements are met",
                "Check available system resources"
            ])
        
        return suggestions
    
    def _should_retry(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if operation should be retried"""
        # Retry for transient errors
        if category == ErrorCategory.DATABASE:
            error_msg = str(error).lower()
            if "locked" in error_msg:
                return True
        
        if category == ErrorCategory.DOCKER:
            error_msg = str(error).lower()
            if "timeout" in error_msg:
                return True
        
        # Don't retry for permanent errors
        if isinstance(error, (FileNotFoundError, PermissionError, yaml.YAMLError)):
            return False
        
        return False
    
    def _should_exit(self, error: Exception, category: ErrorCategory,
                    severity: ErrorSeverity) -> bool:
        """Determine if system should exit"""
        # Exit for critical errors
        if severity == ErrorSeverity.CRITICAL:
            return True
        
        # Exit for Docker daemon not available
        if category == ErrorCategory.DOCKER:
            error_msg = str(error).lower()
            if "not running" in error_msg or "cannot connect" in error_msg:
                return True
        
        # Exit for corrupted database
        if category == ErrorCategory.DATABASE:
            error_msg = str(error).lower()
            if "corrupt" in error_msg:
                return True
        
        return False
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level for severity"""
        if severity == ErrorSeverity.CRITICAL:
            return logging.CRITICAL
        elif severity == ErrorSeverity.ERROR:
            return logging.ERROR
        elif severity == ErrorSeverity.WARNING:
            return logging.WARNING
        else:
            return logging.INFO
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs(self.log_path, exist_ok=True)
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for debugging"""
        state = {}
        
        # Docker status
        try:
            client = docker.from_env()
            client.ping()
            state['docker_available'] = True
            state['docker_version'] = client.version()
        except Exception as e:
            state['docker_available'] = False
            state['docker_error'] = str(e)
        
        # Disk space
        try:
            stat = shutil.disk_usage('/')
            state['disk_total_gb'] = stat.total / (1024**3)
            state['disk_used_gb'] = stat.used / (1024**3)
            state['disk_free_gb'] = stat.free / (1024**3)
            state['disk_percent_used'] = (stat.used / stat.total) * 100
        except Exception as e:
            state['disk_error'] = str(e)
        
        # Python version
        state['python_version'] = sys.version
        
        # Current working directory
        state['cwd'] = os.getcwd()
        
        return state
    
    def format_error_for_user(self, response: ErrorResponse) -> str:
        """
        Format error response for display to user
        
        Args:
            response: ErrorResponse to format
            
        Returns:
            Formatted error message string
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append(f"ERROR: {response.category.value.upper()}")
        lines.append("=" * 70)
        lines.append(f"\n{response.user_message}\n")
        
        if response.recovery_suggestions:
            lines.append("RECOVERY SUGGESTIONS:")
            for i, suggestion in enumerate(response.recovery_suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")
        
        lines.append("=" * 70)
        
        if response.should_exit:
            lines.append("This is a critical error. The program will exit.")
            lines.append("=" * 70)
        
        return "\n".join(lines)


# Convenience functions for common error handling patterns

def handle_docker_error(error: Exception, context: ErrorContext,
                       handler: Optional[ErrorHandler] = None) -> ErrorResponse:
    """Handle Docker-specific errors"""
    if handler is None:
        handler = ErrorHandler()
    return handler.handle_error(error, context)


def handle_database_error(error: Exception, context: ErrorContext,
                          handler: Optional[ErrorHandler] = None,
                          max_retries: int = 3) -> Tuple[bool, Optional[ErrorResponse]]:
    """
    Handle database errors with retry logic
    
    Returns:
        Tuple of (should_retry, error_response)
    """
    if handler is None:
        handler = ErrorHandler()
    
    response = handler.handle_error(error, context)
    
    # Implement retry logic for database locked errors
    if response.should_retry and "locked" in str(error).lower():
        return True, response
    
    return False, response


def handle_validation_error(error: Exception, context: ErrorContext,
                            handler: Optional[ErrorHandler] = None) -> ErrorResponse:
    """Handle validation-specific errors"""
    if handler is None:
        handler = ErrorHandler()
    return handler.handle_error(error, context)
