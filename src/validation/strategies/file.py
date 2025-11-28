from typing import Dict, Any
import re
from ...core.interfaces import ValidatorStrategy, Environment, ValidationResult

class FileStrategy(ValidatorStrategy):
    """Strategy for validating file properties"""
    
    def validate(self, environment: Environment, check_config: Dict[str, Any]) -> ValidationResult:
        path = check_config.get('path')
        should_exist = check_config.get('should_exist', True)
        permissions = check_config.get('permissions')
        owner = check_config.get('owner')
        group = check_config.get('group')
        content_contains = check_config.get('content_contains')
        content_regex = check_config.get('content_regex')
        
        exists = environment.file_exists(path)
        
        if should_exist and not exists:
            return ValidationResult(
                passed=False,
                message="File does not exist",
                expected=f"File {path} should exist",
                actual="File not found"
            )
            
        if not should_exist and exists:
            return ValidationResult(
                passed=False,
                message="File exists but should not",
                expected=f"File {path} should not exist",
                actual="File exists"
            )
            
        if not should_exist:
            return ValidationResult(passed=True, message="File correctly does not exist")
            
        # Check stats if needed
        if permissions or owner or group:
            try:
                stats = environment.get_file_stats(path)
                
                if permissions:
                    # Normalize permissions (remove leading zeros for comparison)
                    expected_perms = str(permissions).lstrip('0')
                    actual_perms = str(stats['permissions']).lstrip('0')
                    if actual_perms != expected_perms:
                        return ValidationResult(
                            passed=False,
                            message="File permissions do not match",
                            expected=f"permissions {permissions}",
                            actual=f"permissions {stats['permissions']}"
                        )
                        
                if owner and stats['owner'] != owner:
                    return ValidationResult(
                        passed=False,
                        message="File owner does not match",
                        expected=f"owner {owner}",
                        actual=f"owner {stats['owner']}"
                    )
                    
                if group and stats['group'] != group:
                    return ValidationResult(
                        passed=False,
                        message="File group does not match",
                        expected=f"group {group}",
                        actual=f"group {stats['group']}"
                    )
            except Exception as e:
                return ValidationResult(
                    passed=False,
                    message=f"Failed to check file stats: {str(e)}"
                )
                
        # Check content if needed
        if content_contains or content_regex:
            try:
                content = environment.read_file(path)
                
                if content_contains and content_contains not in content:
                    return ValidationResult(
                        passed=False,
                        message="File content does not contain expected text",
                        expected=f"content containing: {content_contains}",
                        actual=f"content start: {content[:50]}..."
                    )
                    
                if content_regex and not re.search(content_regex, content):
                    return ValidationResult(
                        passed=False,
                        message="File content does not match regex pattern",
                        expected=f"pattern: {content_regex}",
                        actual=f"content start: {content[:50]}..."
                    )
            except Exception as e:
                return ValidationResult(
                    passed=False,
                    message=f"Failed to check file content: {str(e)}"
                )
                
        return ValidationResult(passed=True, message="File validation passed")
