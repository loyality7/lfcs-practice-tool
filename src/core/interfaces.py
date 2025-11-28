from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Result of a command execution"""
    exit_code: int
    output: str
    error: Optional[str] = None

class Environment(ABC):
    """Abstract base class for execution environments (Docker, SSH, Local)"""
    
    @abstractmethod
    def execute_command(self, command: str, user: Optional[str] = None) -> ExecutionResult:
        """Execute a command in the environment"""
        pass
    
    @abstractmethod
    def read_file(self, path: str) -> str:
        """Read file content from the environment"""
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        pass
    
    @abstractmethod
    def get_file_stats(self, path: str) -> Dict[str, Any]:
        """Get file statistics (permissions, owner, group)"""
        pass

@dataclass
class ValidationResult:
    """Result of a validation check"""
    passed: bool
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ValidatorStrategy(ABC):
    """Abstract base class for validation strategies"""
    
    @abstractmethod
    def validate(self, environment: Environment, check_config: Dict[str, Any]) -> ValidationResult:
        """Run validation using the provided environment"""
        pass
