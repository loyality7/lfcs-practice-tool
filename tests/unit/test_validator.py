"""
Property-based tests for the Validator component
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, MagicMock
import docker

from src.validation.validator import Validator, ValidationResult, CheckResult
from src.core.models import (
    Scenario, ValidationRules, CommandCheck, FileCheck, 
    ServiceCheck, CustomCheck
)
from src.docker_manager.container import DockerManager, ExecutionResult


# Custom strategies for generating validation checks
@st.composite
def command_check_strategy(draw):
    """Generate random CommandCheck objects"""
    command = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00\n')))
    expected_output = draw(st.one_of(st.none(), st.text(max_size=100)))
    expected_exit_code = draw(st.integers(min_value=0, max_value=2))
    regex_match = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return CommandCheck(
        command=command,
        expected_output=expected_output,
        expected_exit_code=expected_exit_code,
        regex_match=regex_match,
        description=description
    )


@st.composite
def file_check_strategy(draw):
    """Generate random FileCheck objects"""
    path = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00\n')))
    should_exist = draw(st.booleans())
    permissions = draw(st.one_of(st.none(), st.sampled_from(['0644', '0755', '0600', '0777'])))
    owner = draw(st.one_of(st.none(), st.sampled_from(['root', 'user', 'alice'])))
    group = draw(st.one_of(st.none(), st.sampled_from(['root', 'users', 'wheel'])))
    content_contains = draw(st.one_of(st.none(), st.text(max_size=50)))
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return FileCheck(
        path=path,
        should_exist=should_exist,
        permissions=permissions,
        owner=owner,
        group=group,
        content_contains=content_contains,
        description=description
    )


@st.composite
def service_check_strategy(draw):
    """Generate random ServiceCheck objects"""
    service_name = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters='\x00\n ')))
    should_be_running = draw(st.booleans())
    should_be_enabled = draw(st.booleans())
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return ServiceCheck(
        service_name=service_name,
        should_be_running=should_be_running,
        should_be_enabled=should_be_enabled,
        description=description
    )


@st.composite
def custom_check_strategy(draw):
    """Generate random CustomCheck objects"""
    script_path = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00\n')))
    args = draw(st.lists(st.text(max_size=20), max_size=5))
    expected_exit_code = draw(st.integers(min_value=0, max_value=2))
    description = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return CustomCheck(
        script_path=script_path,
        args=args,
        expected_exit_code=expected_exit_code,
        description=description
    )


@st.composite
def validation_check_strategy(draw):
    """Generate any type of validation check"""
    check_type = draw(st.sampled_from(['command', 'file', 'service', 'custom']))
    
    if check_type == 'command':
        return draw(command_check_strategy())
    elif check_type == 'file':
        return draw(file_check_strategy())
    elif check_type == 'service':
        return draw(service_check_strategy())
    else:
        return draw(custom_check_strategy())


@st.composite
def scenario_strategy(draw):
    """Generate random Scenario objects with validation rules"""
    scenario_id = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters='\x00\n ')))
    category = draw(st.sampled_from(['networking', 'storage', 'users_groups', 
                                     'operations_deployment', 'essential_commands']))
    difficulty = draw(st.sampled_from(['easy', 'medium', 'hard']))
    task = draw(st.text(min_size=1, max_size=100))
    points = draw(st.integers(min_value=1, max_value=100))
    
    # Generate 1-5 validation checks
    checks = draw(st.lists(validation_check_strategy(), min_size=1, max_size=5))
    validation = ValidationRules(checks=checks)
    
    return Scenario(
        id=scenario_id,
        category=category,
        difficulty=difficulty,
        task=task,
        validation=validation,
        points=points
    )


def create_mock_docker_manager(execution_results):
    """
    Create a mock DockerManager that returns predetermined results
    
    Args:
        execution_results: Dict mapping commands to ExecutionResult objects
    """
    mock_manager = Mock(spec=DockerManager)
    
    def execute_command_side_effect(container, command, timeout=None):
        # Return predetermined result or default
        if command in execution_results:
            return execution_results[command]
        # Default result
        return ExecutionResult(exit_code=0, output="", error=None)
    
    mock_manager.execute_command.side_effect = execute_command_side_effect
    return mock_manager


def create_mock_container():
    """Create a mock Docker container"""
    mock_container = MagicMock(spec=docker.models.containers.Container)
    mock_container.short_id = "test123"
    mock_container.name = "test-container"
    return mock_container


# Feature: lfcs-practice-environment, Property 4: Validation determinism
@settings(max_examples=100)
@given(
    scenario=scenario_strategy(),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_validation_determinism(scenario, seed):
    """
    For any scenario and container state, running validation multiple times 
    on the same unchanged state should produce identical results.
    
    Validates: Requirements 3.1, 3.5
    """
    # Create consistent execution results based on seed
    execution_results = {}
    
    # Build deterministic results for each check
    for i, check in enumerate(scenario.validation.checks):
        if isinstance(check, CommandCheck):
            # Deterministic output based on seed and check index
            output = f"output_{seed}_{i}"
            exit_code = (seed + i) % 3  # 0, 1, or 2
            execution_results[check.command] = ExecutionResult(
                exit_code=exit_code,
                output=output,
                error=None
            )
        elif isinstance(check, FileCheck):
            # File existence check
            exists_output = "exists" if (seed + i) % 2 == 0 else "not_exists"
            execution_results[f"test -e {check.path} && echo 'exists' || echo 'not_exists'"] = ExecutionResult(
                exit_code=0,
                output=exists_output,
                error=None
            )
            # Permissions check
            perms = str((seed + i) % 1000).zfill(3)
            execution_results[f"stat -c '%a' {check.path}"] = ExecutionResult(
                exit_code=0,
                output=perms,
                error=None
            )
            # Owner check
            execution_results[f"stat -c '%U' {check.path}"] = ExecutionResult(
                exit_code=0,
                output=f"owner_{seed}",
                error=None
            )
            # Group check
            execution_results[f"stat -c '%G' {check.path}"] = ExecutionResult(
                exit_code=0,
                output=f"group_{seed}",
                error=None
            )
            # Content check
            execution_results[f"cat {check.path}"] = ExecutionResult(
                exit_code=0,
                output=f"content_{seed}_{i}",
                error=None
            )
        elif isinstance(check, ServiceCheck):
            # Service status checks
            is_active = "active" if (seed + i) % 2 == 0 else "inactive"
            execution_results[f"systemctl is-active {check.service_name}"] = ExecutionResult(
                exit_code=0 if is_active == "active" else 3,
                output=is_active,
                error=None
            )
            is_enabled = "enabled" if (seed + i) % 2 == 1 else "disabled"
            execution_results[f"systemctl is-enabled {check.service_name}"] = ExecutionResult(
                exit_code=0 if is_enabled == "enabled" else 1,
                output=is_enabled,
                error=None
            )
        elif isinstance(check, CustomCheck):
            # Custom script execution
            args_str = ' '.join(check.args) if check.args else ''
            command = f"{check.script_path} {args_str}".strip()
            execution_results[command] = ExecutionResult(
                exit_code=(seed + i) % 3,
                output=f"custom_output_{seed}_{i}",
                error=None
            )
    
    # Create mock components
    mock_docker_manager = create_mock_docker_manager(execution_results)
    mock_container = create_mock_container()
    
    # Create validator
    validator = Validator(mock_docker_manager)
    
    # Run validation multiple times
    result1 = validator.validate(mock_container, scenario)
    result2 = validator.validate(mock_container, scenario)
    result3 = validator.validate(mock_container, scenario)
    
    # Assert determinism: all results should be identical
    assert result1.passed == result2.passed == result3.passed, \
        "Validation pass/fail status should be deterministic"
    
    assert result1.checks_passed == result2.checks_passed == result3.checks_passed, \
        "Number of checks passed should be deterministic"
    
    assert result1.checks_total == result2.checks_total == result3.checks_total, \
        "Total number of checks should be deterministic"
    
    assert len(result1.check_results) == len(result2.check_results) == len(result3.check_results), \
        "Number of check results should be deterministic"
    
    # Compare individual check results
    for i in range(len(result1.check_results)):
        assert result1.check_results[i].passed == result2.check_results[i].passed == result3.check_results[i].passed, \
            f"Check {i} pass/fail status should be deterministic"
        
        assert result1.check_results[i].check_name == result2.check_results[i].check_name == result3.check_results[i].check_name, \
            f"Check {i} name should be deterministic"
    
    # Feedback should also be identical
    assert result1.feedback == result2.feedback == result3.feedback, \
        "Validation feedback should be deterministic"



# Feature: lfcs-practice-environment, Property 5: Validation feedback completeness
@settings(max_examples=100)
@given(
    scenario=scenario_strategy(),
    seed=st.integers(min_value=0, max_value=1000000)
)
def test_validation_feedback_completeness(scenario, seed):
    """
    For any failed validation, the feedback should identify which specific checks 
    failed and provide actionable information about what was expected versus what was found.
    
    Validates: Requirements 3.3, 3.4
    """
    # Create execution results that will cause some checks to fail
    execution_results = {}
    
    # Track which checks should fail
    expected_failures = []
    
    # Build results that cause failures
    for i, check in enumerate(scenario.validation.checks):
        # Make every other check fail (deterministically based on seed)
        should_fail = (seed + i) % 2 == 0
        
        if isinstance(check, CommandCheck):
            # Make command unique per check to avoid collisions
            unique_command = f"{check.command}_check{i}"
            check.command = unique_command
            
            if should_fail:
                # Wrong exit code to cause failure
                exit_code = (check.expected_exit_code + 1) % 3
                output = "wrong_output"
                expected_failures.append(i)
            else:
                exit_code = check.expected_exit_code
                # Provide output that matches all conditions
                if check.expected_output is not None:
                    output = check.expected_output
                elif check.regex_match:
                    # Provide output that matches the regex
                    output = check.regex_match  # Simple match
                else:
                    output = "correct_output"
            
            execution_results[unique_command] = ExecutionResult(
                exit_code=exit_code,
                output=output,
                error=None
            )
            
        elif isinstance(check, FileCheck):
            # Make path unique per check to avoid collisions
            unique_path = f"{check.path}_check{i}"
            check.path = unique_path
            
            if should_fail:
                # File doesn't exist when it should (or vice versa)
                # Invert the expected state to cause failure
                if check.should_exist:
                    exists_output = "not_exists"  # File should exist but doesn't
                else:
                    exists_output = "exists"  # File shouldn't exist but does
                expected_failures.append(i)
            else:
                # Match the expected state to pass
                if check.should_exist:
                    exists_output = "exists"  # File should exist and does
                else:
                    exists_output = "not_exists"  # File shouldn't exist and doesn't
            
            execution_results[f"test -e {unique_path} && echo 'exists' || echo 'not_exists'"] = ExecutionResult(
                exit_code=0,
                output=exists_output,
                error=None
            )
            
            # Only add other file check results if file should exist
            if exists_output == "exists":
                execution_results[f"stat -c '%a' {unique_path}"] = ExecutionResult(
                    exit_code=0,
                    output=check.permissions.lstrip('0') if check.permissions else "644",
                    error=None
                )
                execution_results[f"stat -c '%U' {unique_path}"] = ExecutionResult(
                    exit_code=0,
                    output=check.owner if check.owner else "root",
                    error=None
                )
                execution_results[f"stat -c '%G' {unique_path}"] = ExecutionResult(
                    exit_code=0,
                    output=check.group if check.group else "root",
                    error=None
                )
                execution_results[f"cat {unique_path}"] = ExecutionResult(
                    exit_code=0,
                    output=check.content_contains if check.content_contains else "file content",
                    error=None
                )
            
        elif isinstance(check, ServiceCheck):
            # Make service name unique per check to avoid collisions
            unique_service_name = f"{check.service_name}_check{i}"
            # Update the check to use unique name
            check.service_name = unique_service_name
            
            if should_fail:
                # Service not running when it should be
                is_active = "inactive" if check.should_be_running else "active"
                exit_code = 3 if check.should_be_running else 0
                expected_failures.append(i)
            else:
                is_active = "active" if check.should_be_running else "inactive"
                exit_code = 0 if check.should_be_running else 3
            
            execution_results[f"systemctl is-active {unique_service_name}"] = ExecutionResult(
                exit_code=exit_code,
                output=is_active,
                error=None
            )
            
            is_enabled = "enabled" if check.should_be_enabled else "disabled"
            execution_results[f"systemctl is-enabled {unique_service_name}"] = ExecutionResult(
                exit_code=0 if check.should_be_enabled else 1,
                output=is_enabled,
                error=None
            )
            
        elif isinstance(check, CustomCheck):
            # Make script path unique per check to avoid collisions
            unique_script_path = f"{check.script_path}_check{i}"
            check.script_path = unique_script_path
            
            if should_fail:
                # Wrong exit code
                exit_code = (check.expected_exit_code + 1) % 3
                expected_failures.append(i)
            else:
                exit_code = check.expected_exit_code
            
            args_str = ' '.join(check.args) if check.args else ''
            command = f"{unique_script_path} {args_str}".strip()
            execution_results[command] = ExecutionResult(
                exit_code=exit_code,
                output=f"custom_output_{seed}_{i}",
                error=None
            )
    
    # Create mock components
    mock_docker_manager = create_mock_docker_manager(execution_results)
    mock_container = create_mock_container()
    
    # Create validator
    validator = Validator(mock_docker_manager)
    
    # Run validation
    result = validator.validate(mock_container, scenario)
    
    # If there are expected failures, validation should not pass
    if expected_failures:
        assert not result.passed, "Validation should fail when checks fail"
        
        # Check that feedback is provided
        assert result.feedback, "Feedback should be provided for failed validation"
        assert len(result.feedback) > 0, "Feedback should not be empty"
        
        # Check that failed checks are identified in check_results
        failed_check_results = [cr for cr in result.check_results if not cr.passed]
        assert len(failed_check_results) > 0, "Failed checks should be identified in check_results"
        
        # For each failed check, verify completeness of feedback
        for check_result in failed_check_results:
            # Check name should be present
            assert check_result.check_name, "Failed check should have a name"
            
            # Message should be present
            assert check_result.message, "Failed check should have a message"
            
            # For failed checks, expected or actual should be present to provide actionable info
            # (at least one should be present to help user understand what went wrong)
            has_actionable_info = (
                check_result.expected is not None or 
                check_result.actual is not None or
                "error" in check_result.message.lower() or
                "failed" in check_result.message.lower()
            )
            assert has_actionable_info, \
                f"Failed check '{check_result.check_name}' should provide actionable information"
        
        # Verify feedback contains information about failures
        feedback_lower = result.feedback.lower()
        assert "fail" in feedback_lower or "error" in feedback_lower, \
            "Feedback should indicate that checks failed"
        
        # Verify feedback shows the count of passed/failed checks
        assert str(result.checks_passed) in result.feedback, \
            "Feedback should show number of checks passed"
        assert str(result.checks_total) in result.feedback, \
            "Feedback should show total number of checks"
    else:
        # All checks should pass
        assert result.passed, "Validation should pass when all checks pass"
        assert result.checks_passed == result.checks_total, \
            "All checks should be marked as passed"



def test_mock_setup_debug():
    """Debug test to verify mock setup works correctly"""
    execution_results = {
        "test -e 0 && echo 'exists' || echo 'not_exists'": ExecutionResult(
            exit_code=0,
            output="not_exists",
            error=None
        )
    }
    
    mock_manager = create_mock_docker_manager(execution_results)
    mock_container = create_mock_container()
    
    result = mock_manager.execute_command(mock_container, "test -e 0 && echo 'exists' || echo 'not_exists'")
    
    print(f"Result: {result}")
    print(f"Output: '{result.output}'")
    print(f"'exists' in output: {'exists' in result.output}")
    
    assert result.output == "not_exists", f"Expected 'not_exists', got '{result.output}'"
