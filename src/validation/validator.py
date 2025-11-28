import logging
from typing import Dict, List, Any

from ..core.models import Scenario, ValidationResult as ModelValidationResult, CheckResult
from ..core.interfaces import Environment, ValidatorStrategy
from .strategies import CommandStrategy, FileStrategy, ServiceStrategy

logger = logging.getLogger(__name__)

class Validator:
    """
    Validates task completion using pluggable strategies
    """
    
    def __init__(self):
        self.strategies: Dict[str, ValidatorStrategy] = {
            'command': CommandStrategy(),
            'file': FileStrategy(),
            'service': ServiceStrategy()
        }
    
    def validate(self, environment: Environment, scenario: Scenario) -> ModelValidationResult:
        """
        Run all validation checks for a scenario
        """
        logger.info(f"Starting validation for scenario {scenario.id}")
        
        check_results = []
        checks_passed = 0
        checks_total = len(scenario.validation.checks)
        
        for i, check in enumerate(scenario.validation.checks):
            # Convert check to dict for strategy
            check_config = check.to_dict()
            check_type = check_config.get('type')
            check_name = check_config.get('description') or f"Check {i+1}"
            
            strategy = self.strategies.get(check_type)
            
            if not strategy:
                logger.warning(f"No strategy found for check type: {check_type}")
                result = CheckResult(
                    check_name=check_name,
                    passed=False,
                    message=f"Unknown or disabled check type: {check_type}"
                )
            else:
                try:
                    # Execute validation strategy
                    val_result = strategy.validate(environment, check_config)
                    
                    # Convert interface ValidationResult to model CheckResult
                    result = CheckResult(
                        check_name=check_name,
                        passed=val_result.passed,
                        message=val_result.message,
                        expected=val_result.expected,
                        actual=val_result.actual
                    )
                except Exception as e:
                    logger.error(f"Error executing check {check_name}: {e}")
                    result = CheckResult(
                        check_name=check_name,
                        passed=False,
                        message=f"Check failed with error: {str(e)}"
                    )
            
            check_results.append(result)
            if result.passed:
                checks_passed += 1
                
        # Determine overall pass/fail
        passed = checks_passed == checks_total
        
        # Generate feedback
        feedback = self._generate_feedback(check_results, checks_passed, checks_total)
        
        return ModelValidationResult(
            passed=passed,
            checks_passed=checks_passed,
            checks_total=checks_total,
            check_results=check_results,
            feedback=feedback
        )

    def _generate_feedback(self, check_results: List[CheckResult], 
                          checks_passed: int, checks_total: int) -> str:
        """Generate detailed feedback message"""
        lines = []
        lines.append(f"\nValidation Results: {checks_passed}/{checks_total} checks passed\n")
        lines.append("=" * 60)
        
        for result in check_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"\n{status}: {result.check_name}")
            lines.append(f"  {result.message}")
            
            if result.expected:
                lines.append(f"  Expected: {result.expected}")
            
            if result.actual:
                lines.append(f"  Actual: {result.actual}")
        
        lines.append("\n" + "=" * 60)
        
        if checks_passed == checks_total:
            lines.append("✓ All checks passed! Great job!")
        else:
            failed_count = checks_total - checks_passed
            lines.append(f"✗ {failed_count} check(s) failed. Review the feedback above.")
        
        return "\n".join(lines)
