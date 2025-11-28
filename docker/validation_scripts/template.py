#!/usr/bin/env python3
"""
Python Validation Script Template

This template provides a standard structure for custom validation scripts.
Validation scripts are executed inside Docker containers to verify task completion.

INTERFACE:
- Exit code 0 indicates validation passed
- Exit code non-zero indicates validation failed
- Output to stdout is captured and displayed to the user
- Arguments can be passed from the scenario YAML file

USAGE:
The script receives arguments from the CustomCheck in the scenario:
  args:
    - arg1
    - arg2

EXAMPLE SCENARIO YAML:
  validation:
    checks:
      - type: custom
        script_path: /validation/my_script.py
        args: ["expected_value", "threshold"]
        expected_exit_code: 0
        description: "Custom validation for complex scenario"
"""

import sys
import os
import subprocess
from typing import List, Optional


def validate_pass(message: str) -> None:
    """Print success message and exit with code 0"""
    print(f"✓ Validation passed: {message}")
    sys.exit(0)


def validate_fail(message: str) -> None:
    """Print failure message and exit with code 1"""
    print(f"✗ Validation failed: {message}")
    sys.exit(1)


def run_command(command: str) -> tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, stderr
    
    Args:
        command: Shell command to execute
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def file_exists(path: str) -> bool:
    """Check if a file exists"""
    return os.path.exists(path)


def file_contains(path: str, text: str) -> bool:
    """Check if a file contains specific text"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            return text in content
    except Exception:
        return False


def main(args: List[str]) -> None:
    """
    Main validation logic
    
    Args:
        args: Command line arguments passed to the script
    """
    # Parse arguments
    # arg1 = args[0] if len(args) > 0 else "default_value"
    # arg2 = args[1] if len(args) > 1 else "default_value"
    
    # Example validation checks:
    
    # Check if a file exists
    # if not file_exists("/path/to/file"):
    #     validate_fail("Required file not found")
    
    # Check if a command succeeds
    # exit_code, stdout, stderr = run_command("some_command")
    # if exit_code != 0:
    #     validate_fail(f"Command failed: {stderr}")
    
    # Check if output matches expected
    # exit_code, stdout, stderr = run_command("some_command")
    # expected = "expected_output"
    # if stdout.strip() != expected:
    #     validate_fail(f"Expected '{expected}' but got '{stdout.strip()}'")
    
    # Check if file contains expected text
    # if not file_contains("/path/to/file", "expected text"):
    #     validate_fail("File does not contain expected text")
    
    # If all checks pass
    validate_pass("All validation checks completed successfully")


if __name__ == "__main__":
    # Get command line arguments (excluding script name)
    args = sys.argv[1:]
    main(args)
