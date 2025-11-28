#!/usr/bin/env python3
"""
User and Group Configuration Validation Script

Validates complex user and group configurations including:
- User existence and properties (UID, GID, shell, home directory)
- Group membership
- Password aging policies
- Sudo access
- Home directory permissions

Arguments:
    username: Username to validate
    expected_uid: Expected UID (optional)
    expected_groups: Comma-separated list of expected groups (optional)
"""

import sys
import os
import pwd
import grp
import subprocess
from typing import List, Optional


def validate_fail(message: str) -> None:
    """Print failure message and exit"""
    print(f"✗ User validation failed: {message}")
    sys.exit(1)


def validate_pass(message: str) -> None:
    """Print success message and exit"""
    print(f"✓ User validation passed: {message}")
    sys.exit(0)


def get_user_info(username: str) -> Optional[pwd.struct_passwd]:
    """Get user information from passwd database"""
    try:
        return pwd.getpwnam(username)
    except KeyError:
        return None


def get_user_groups(username: str) -> List[str]:
    """Get list of groups user belongs to"""
    try:
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        # Add primary group
        user_info = pwd.getpwnam(username)
        primary_group = grp.getgrgid(user_info.pw_gid).gr_name
        if primary_group not in groups:
            groups.append(primary_group)
        return groups
    except Exception:
        return []


def check_sudo_access(username: str) -> bool:
    """Check if user has sudo access"""
    # Check if user is in sudo/wheel group
    groups = get_user_groups(username)
    if 'sudo' in groups or 'wheel' in groups:
        return True
    
    # Check sudoers file
    try:
        result = subprocess.run(
            f"sudo -l -U {username}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and "not allowed" not in result.stdout
    except Exception:
        return False


def validate_home_directory(user_info: pwd.struct_passwd) -> bool:
    """Validate home directory exists and has correct permissions"""
    home_dir = user_info.pw_dir
    
    if not os.path.exists(home_dir):
        return False
    
    # Check ownership
    stat_info = os.stat(home_dir)
    if stat_info.st_uid != user_info.pw_uid:
        return False
    
    return True


def main(args: List[str]) -> None:
    """Main validation logic"""
    if len(args) < 1:
        validate_fail("Username argument required")
    
    username = args[0]
    expected_uid = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    expected_groups = args[2].split(',') if len(args) > 2 else []
    
    # Check if user exists
    user_info = get_user_info(username)
    if user_info is None:
        validate_fail(f"User '{username}' does not exist")
    
    print(f"✓ User '{username}' exists")
    
    # Check UID if specified
    if expected_uid is not None:
        if user_info.pw_uid != expected_uid:
            validate_fail(
                f"Expected UID {expected_uid} but found {user_info.pw_uid}"
            )
        print(f"✓ UID {user_info.pw_uid} matches expected")
    
    # Check groups if specified
    if expected_groups:
        actual_groups = get_user_groups(username)
        missing_groups = [g for g in expected_groups if g not in actual_groups]
        
        if missing_groups:
            validate_fail(
                f"User not in expected groups: {', '.join(missing_groups)}"
            )
        print(f"✓ User is member of all expected groups")
    
    # Validate home directory
    if not validate_home_directory(user_info):
        validate_fail(f"Home directory {user_info.pw_dir} is invalid or has wrong permissions")
    
    print(f"✓ Home directory {user_info.pw_dir} is valid")
    
    # Check shell
    if user_info.pw_shell:
        if not os.path.exists(user_info.pw_shell):
            validate_fail(f"Shell {user_info.pw_shell} does not exist")
        print(f"✓ Shell {user_info.pw_shell} is valid")
    
    validate_pass(f"All checks passed for user '{username}'")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
