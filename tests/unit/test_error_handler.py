"""
Unit tests for Error Handler
"""

import pytest
import sqlite3
import docker
from docker.errors import DockerException, ImageNotFound, APIError
import yaml

from src.utils.error_handler import (
    ErrorHandler, ErrorContext, ErrorCategory, ErrorSeverity,
    handle_docker_error, handle_database_error, handle_validation_error
)


class TestErrorHandlerBasics:
    """Test basic error handler functionality"""
    
    def test_error_handler_initialization(self):
        """Test error handler can be initialized"""
        handler = ErrorHandler()
        assert handler is not None
        assert handler.log_path == "logs"
    
    def test_error_handler_with_custom_log_path(self):
        """Test error handler with custom log path"""
        handler = ErrorHandler(log_path="custom/logs")
        assert handler.log_path == "custom/logs"


class TestErrorCategorization:
    """Test error categorization"""
    
    def test_categorize_docker_error(self):
        """Test Docker errors are categorized correctly"""
        handler = ErrorHandler()
        error = DockerException("Docker daemon not running")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.category == ErrorCategory.DOCKER
    
    def test_categorize_database_error(self):
        """Test database errors are categorized correctly"""
        handler = ErrorHandler()
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.category == ErrorCategory.DATABASE
    
    def test_categorize_yaml_error(self):
        """Test YAML errors are categorized correctly"""
        handler = ErrorHandler()
        error = yaml.YAMLError("invalid yaml syntax")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.category == ErrorCategory.SCENARIO
    
    def test_categorize_file_not_found_error(self):
        """Test file not found errors are categorized correctly"""
        handler = ErrorHandler()
        error = FileNotFoundError("file not found")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.category == ErrorCategory.SYSTEM


class TestErrorSeverity:
    """Test error severity determination"""
    
    def test_docker_daemon_not_running_is_critical(self):
        """Test Docker daemon not running is critical"""
        handler = ErrorHandler()
        error = DockerException("Docker daemon is not running")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.severity == ErrorSeverity.CRITICAL
        assert response.should_exit is True
    
    def test_database_locked_is_error(self):
        """Test database locked is error level"""
        handler = ErrorHandler()
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.severity == ErrorSeverity.ERROR
    
    def test_permission_error_is_critical(self):
        """Test permission errors are critical"""
        handler = ErrorHandler()
        error = PermissionError("permission denied")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.severity == ErrorSeverity.CRITICAL


class TestUserMessages:
    """Test user-friendly error messages"""
    
    def test_docker_not_running_message(self):
        """Test Docker not running message is user-friendly"""
        handler = ErrorHandler()
        error = DockerException("Cannot connect to Docker daemon")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert "Docker daemon" in response.user_message
        assert "not running" in response.user_message or "not accessible" in response.user_message
    
    def test_image_not_found_message(self):
        """Test image not found message is user-friendly"""
        handler = ErrorHandler()
        error = ImageNotFound("Image not found")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert "image" in response.user_message.lower()
        assert "not found" in response.user_message.lower()
    
    def test_database_locked_message(self):
        """Test database locked message is user-friendly"""
        handler = ErrorHandler()
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert "locked" in response.user_message.lower()


class TestRecoverySuggestions:
    """Test recovery suggestions"""
    
    def test_docker_not_running_suggestions(self):
        """Test Docker not running provides recovery suggestions"""
        handler = ErrorHandler()
        error = DockerException("Docker daemon is not running")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert len(response.recovery_suggestions) > 0
        assert any("install" in s.lower() or "start" in s.lower() 
                  for s in response.recovery_suggestions)
    
    def test_image_not_found_suggestions(self):
        """Test image not found provides recovery suggestions"""
        handler = ErrorHandler()
        error = ImageNotFound("Image not found")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert len(response.recovery_suggestions) > 0
        assert any("build" in s.lower() or "pull" in s.lower() 
                  for s in response.recovery_suggestions)
    
    def test_database_locked_suggestions(self):
        """Test database locked provides recovery suggestions"""
        handler = ErrorHandler()
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert len(response.recovery_suggestions) > 0
        assert any("wait" in s.lower() or "retry" in s.lower() 
                  for s in response.recovery_suggestions)


class TestRetryLogic:
    """Test retry logic"""
    
    def test_database_locked_should_retry(self):
        """Test database locked errors should retry"""
        handler = ErrorHandler()
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.should_retry is True
    
    def test_file_not_found_should_not_retry(self):
        """Test file not found errors should not retry"""
        handler = ErrorHandler()
        error = FileNotFoundError("file not found")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.should_retry is False
    
    def test_docker_timeout_should_retry(self):
        """Test Docker timeout errors should retry"""
        handler = ErrorHandler()
        error = APIError("timeout waiting for container")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        assert response.should_retry is True


class TestContextHandling:
    """Test error context handling"""
    
    def test_context_with_scenario_id(self):
        """Test error context includes scenario ID"""
        handler = ErrorHandler()
        error = ValueError("test error")
        context = ErrorContext(
            scenario_id="test_scenario_01",
            user_action="test"
        )
        
        response = handler.handle_error(error, context)
        assert response.context.scenario_id == "test_scenario_01"
    
    def test_context_with_container_id(self):
        """Test error context includes container ID"""
        handler = ErrorHandler()
        error = ValueError("test error")
        context = ErrorContext(
            container_id="abc123",
            user_action="test"
        )
        
        response = handler.handle_error(error, context)
        assert response.context.container_id == "abc123"
    
    def test_context_with_additional_info(self):
        """Test error context includes additional info"""
        handler = ErrorHandler()
        error = ValueError("test error")
        context = ErrorContext(
            user_action="test",
            additional_info={'key': 'value'}
        )
        
        response = handler.handle_error(error, context)
        assert response.context.additional_info == {'key': 'value'}


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_handle_docker_error_function(self):
        """Test handle_docker_error convenience function"""
        error = DockerException("test error")
        context = ErrorContext(user_action="test")
        
        response = handle_docker_error(error, context)
        assert response.category == ErrorCategory.DOCKER
    
    def test_handle_database_error_function(self):
        """Test handle_database_error convenience function"""
        error = sqlite3.OperationalError("database is locked")
        context = ErrorContext(user_action="test")
        
        should_retry, response = handle_database_error(error, context)
        assert response.category == ErrorCategory.DATABASE
        assert should_retry is True
    
    def test_handle_validation_error_function(self):
        """Test handle_validation_error convenience function"""
        error = ValueError("validation failed")
        context = ErrorContext(user_action="test")
        
        response = handle_validation_error(error, context)
        assert response is not None


class TestErrorFormatting:
    """Test error message formatting"""
    
    def test_format_error_for_user(self):
        """Test error formatting for user display"""
        handler = ErrorHandler()
        error = ValueError("test error")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        formatted = handler.format_error_for_user(response)
        
        assert "ERROR" in formatted
        assert "=" in formatted  # Should have separator lines
        assert len(formatted) > 0
    
    def test_format_includes_suggestions(self):
        """Test formatted error includes suggestions"""
        handler = ErrorHandler()
        error = DockerException("Docker daemon is not running")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        formatted = handler.format_error_for_user(response)
        
        assert "RECOVERY SUGGESTIONS" in formatted or "SUGGESTIONS" in formatted.upper()
    
    def test_format_includes_exit_warning(self):
        """Test formatted error includes exit warning for critical errors"""
        handler = ErrorHandler()
        error = DockerException("Docker daemon is not running")
        context = ErrorContext(user_action="test")
        
        response = handler.handle_error(error, context)
        formatted = handler.format_error_for_user(response)
        
        if response.should_exit:
            assert "critical" in formatted.lower() or "exit" in formatted.lower()


class TestSystemState:
    """Test system state collection"""
    
    def test_get_system_state(self):
        """Test system state collection"""
        handler = ErrorHandler()
        state = handler._get_system_state()
        
        assert 'python_version' in state
        assert 'cwd' in state
        # Docker and disk info may or may not be available
        assert isinstance(state, dict)
