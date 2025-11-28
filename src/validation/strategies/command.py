from typing import Dict, Any
import re
from ...core.interfaces import ValidatorStrategy, Environment, ValidationResult

class CommandStrategy(ValidatorStrategy):
    """Strategy for validating command execution"""
    
    def validate(self, environment: Environment, check_config: Dict[str, Any]) -> ValidationResult:
        command = check_config.get('command')
        expected_exit_code = check_config.get('expected_exit_code', 0)
        expected_output = check_config.get('expected_output')
        regex_match = check_config.get('regex_match')
        
        result = environment.execute_command(command)
        
        # Check exit code
        if result.exit_code != expected_exit_code:
            return ValidationResult(
                passed=False,
                message="Exit code mismatch",
                expected=f"exit code {expected_exit_code}",
                actual=f"exit code {result.exit_code}",
                details={"output": result.output, "error": result.error}
            )
            
        # Check output if specified
        if expected_output is not None:
            # Normalize whitespace for robust comparison
            norm_actual = ' '.join(result.output.strip().split())
            norm_expected = ' '.join(expected_output.strip().split())
            
            if norm_actual != norm_expected:
                return ValidationResult(
                    passed=False,
                    message="Output does not match expected",
                    expected=expected_output,
                    actual=result.output.strip()
                )
                
        # Check regex match if specified
        if regex_match is not None:
            if not re.search(regex_match, result.output):
                return ValidationResult(
                    passed=False,
                    message="Output does not match regex pattern",
                    expected=f"pattern: {regex_match}",
                    actual=result.output.strip()
                )
                
        return ValidationResult(
            passed=True,
            message="Command executed successfully",
            actual=result.output.strip()
        )
