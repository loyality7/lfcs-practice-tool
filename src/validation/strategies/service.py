from typing import Dict, Any
from ...core.interfaces import ValidatorStrategy, Environment, ValidationResult

class ServiceStrategy(ValidatorStrategy):
    """Strategy for validating system services"""
    
    def validate(self, environment: Environment, check_config: Dict[str, Any]) -> ValidationResult:
        service_name = check_config.get('service_name')
        should_be_running = check_config.get('should_be_running', True)
        should_be_enabled = check_config.get('should_be_enabled', True)
        
        # Check running status
        result = environment.execute_command(f"systemctl is-active {service_name}")
        is_running = result.exit_code == 0 and 'active' in result.output
        
        if should_be_running and not is_running:
            return ValidationResult(
                passed=False,
                message="Service is not running",
                expected=f"Service {service_name} should be active",
                actual=f"Service status: {result.output.strip()}"
            )
            
        if not should_be_running and is_running:
            return ValidationResult(
                passed=False,
                message="Service is running but should not be",
                expected=f"Service {service_name} should not be active",
                actual="Service is active"
            )
            
        # Check enabled status
        result = environment.execute_command(f"systemctl is-enabled {service_name}")
        is_enabled = result.exit_code == 0 and 'enabled' in result.output
        
        if should_be_enabled and not is_enabled:
            return ValidationResult(
                passed=False,
                message="Service is not enabled",
                expected=f"Service {service_name} should be enabled",
                actual=f"Service enabled status: {result.output.strip()}"
            )
            
        return ValidationResult(passed=True, message="Service validation passed")
