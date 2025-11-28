"""
Data models for scenarios and validation rules
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
from enum import Enum


class CheckType(Enum):
    """Types of validation checks"""
    COMMAND = "command"
    FILE = "file"
    SERVICE = "service"
    CUSTOM = "custom"


@dataclass
class CommandCheck:
    """Command-based validation check"""
    command: str
    expected_output: Optional[str] = None
    expected_exit_code: int = 0
    regex_match: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': 'command',
            'command': self.command,
            'expected_output': self.expected_output,
            'expected_exit_code': self.expected_exit_code,
            'regex_match': self.regex_match,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandCheck':
        """Create from dictionary"""
        return cls(
            command=data['command'],
            expected_output=data.get('expected_output'),
            expected_exit_code=data.get('expected_exit_code', 0),
            regex_match=data.get('regex_match'),
            description=data.get('description')
        )


@dataclass
class FileCheck:
    """File-based validation check"""
    path: str
    should_exist: bool = True
    permissions: Optional[str] = None  # e.g., "0644"
    owner: Optional[str] = None
    group: Optional[str] = None
    content_contains: Optional[str] = None
    content_regex: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': 'file',
            'path': self.path,
            'should_exist': self.should_exist,
            'permissions': self.permissions,
            'owner': self.owner,
            'group': self.group,
            'content_contains': self.content_contains,
            'content_regex': self.content_regex,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileCheck':
        """Create from dictionary"""
        return cls(
            path=data['path'],
            should_exist=data.get('should_exist', True),
            permissions=data.get('permissions'),
            owner=data.get('owner'),
            group=data.get('group'),
            content_contains=data.get('content_contains'),
            content_regex=data.get('content_regex'),
            description=data.get('description')
        )


@dataclass
class ServiceCheck:
    """Service-based validation check"""
    service_name: str
    should_be_running: bool = True
    should_be_enabled: bool = True
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': 'service',
            'service_name': self.service_name,
            'should_be_running': self.should_be_running,
            'should_be_enabled': self.should_be_enabled,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceCheck':
        """Create from dictionary"""
        return cls(
            service_name=data['service_name'],
            should_be_running=data.get('should_be_running', True),
            should_be_enabled=data.get('should_be_enabled', True),
            description=data.get('description')
        )


@dataclass
class CustomCheck:
    """Custom script-based validation check"""
    script_path: str
    args: List[str] = field(default_factory=list)
    expected_exit_code: int = 0
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': 'custom',
            'script_path': self.script_path,
            'args': self.args,
            'expected_exit_code': self.expected_exit_code,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomCheck':
        """Create from dictionary"""
        return cls(
            script_path=data['script_path'],
            args=data.get('args', []),
            expected_exit_code=data.get('expected_exit_code', 0),
            description=data.get('description')
        )


# Type alias for any validation check
ValidationCheck = Union[CommandCheck, FileCheck, ServiceCheck, CustomCheck]


@dataclass
class ValidationRules:
    """Collection of validation rules for a scenario"""
    checks: List[ValidationCheck] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'checks': [check.to_dict() for check in self.checks]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRules':
        """Create from dictionary"""
        checks = []
        for check_data in data.get('checks', []):
            check_type = check_data.get('type')
            if check_type == 'command':
                checks.append(CommandCheck.from_dict(check_data))
            elif check_type == 'file':
                checks.append(FileCheck.from_dict(check_data))
            elif check_type == 'service':
                checks.append(ServiceCheck.from_dict(check_data))
            elif check_type == 'custom':
                checks.append(CustomCheck.from_dict(check_data))
            else:
                raise ValueError(f"Unknown check type: {check_type}")
        
        return cls(checks=checks)


@dataclass
class Scenario:
    """
    Represents a practice scenario
    """
    id: str
    category: str
    difficulty: str  # easy, medium, hard
    task: str  # Description shown to user
    validation: ValidationRules
    points: int
    distribution: Optional[str] = None  # ubuntu, centos, rocky, or None for all
    setup_commands: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None  # seconds
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'difficulty': self.difficulty,
            'task': self.task,
            'validation': self.validation.to_dict(),
            'points': self.points,
            'distribution': self.distribution,
            'setup_commands': self.setup_commands,
            'hints': self.hints,
            'time_limit': self.time_limit,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scenario':
        """Create from dictionary"""
        # Validate required fields
        required_fields = ['id', 'category', 'difficulty', 'task', 'validation', 'points']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Parse validation rules
        validation_data = data['validation']
        if isinstance(validation_data, dict):
            validation = ValidationRules.from_dict(validation_data)
        else:
            raise ValueError("validation must be a dictionary")
        
        return cls(
            id=data['id'],
            category=data['category'],
            difficulty=data['difficulty'],
            task=data['task'],
            validation=validation,
            points=data['points'],
            distribution=data.get('distribution'),
            setup_commands=data.get('setup_commands', []),
            hints=data.get('hints', []),
            time_limit=data.get('time_limit'),
            tags=data.get('tags', [])
        )
    
    def validate_structure(self) -> List[str]:
        """
        Validate scenario structure and return list of errors
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate ID
        if not self.id or not isinstance(self.id, str):
            errors.append("id must be a non-empty string")
        
        # Validate category
        valid_categories = ['networking', 'storage', 'users_groups', 
                          'operations_deployment', 'essential_commands']
        if self.category not in valid_categories:
            errors.append(f"category must be one of: {', '.join(valid_categories)}")
        
        # Validate difficulty
        valid_difficulties = ['easy', 'medium', 'hard']
        if self.difficulty not in valid_difficulties:
            errors.append(f"difficulty must be one of: {', '.join(valid_difficulties)}")
        
        # Validate task description
        if not self.task or not isinstance(self.task, str):
            errors.append("task must be a non-empty string")
        
        # Validate points
        if not isinstance(self.points, int) or self.points <= 0:
            errors.append("points must be a positive integer")
        
        # Validate distribution if specified
        if self.distribution:
            valid_distributions = ['ubuntu', 'centos', 'rocky']
            if self.distribution not in valid_distributions:
                errors.append(f"distribution must be one of: {', '.join(valid_distributions)}")
        
        # Validate validation rules
        if not self.validation.checks:
            errors.append("validation must contain at least one check")
        
        # Validate time limit if specified
        if self.time_limit is not None:
            if not isinstance(self.time_limit, int) or self.time_limit <= 0:
                errors.append("time_limit must be a positive integer")
        
        return errors

@dataclass
class CheckResult:
    """Result of a single validation check"""
    check_name: str
    passed: bool
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validating a scenario"""
    passed: bool
    checks_passed: int
    checks_total: int
    check_results: List[CheckResult] = field(default_factory=list)
    feedback: str = ""
