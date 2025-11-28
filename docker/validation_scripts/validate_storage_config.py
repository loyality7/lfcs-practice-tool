#!/usr/bin/env python3
"""
Storage Configuration Validation Script

Validates complex storage configurations including:
- Filesystem mounts and mount options
- Disk partitions and sizes
- LVM configuration (PV, VG, LV)
- Filesystem types and usage
- Mount point permissions

Arguments:
    mount_point: Mount point to validate (e.g., /mnt/data)
    expected_fstype: Expected filesystem type (optional, e.g., ext4, xfs)
    expected_device: Expected device (optional, e.g., /dev/sdb1)
"""

import sys
import os
import subprocess
import re
from typing import Optional, Dict, List


def validate_fail(message: str) -> None:
    """Print failure message and exit"""
    print(f"✗ Storage validation failed: {message}")
    sys.exit(1)


def validate_pass(message: str) -> None:
    """Print success message and exit"""
    print(f"✓ Storage validation passed: {message}")
    sys.exit(0)


def run_command(command: str) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_mount_info(mount_point: str) -> Optional[Dict[str, str]]:
    """Get mount information for a mount point"""
    exit_code, stdout, _ = run_command("mount")
    if exit_code != 0:
        return None
    
    for line in stdout.split('\n'):
        if mount_point in line:
            # Parse mount line: device on mount_point type fstype (options)
            match = re.match(r'(.+?) on (.+?) type (.+?) \((.+?)\)', line)
            if match:
                return {
                    'device': match.group(1),
                    'mount_point': match.group(2),
                    'fstype': match.group(3),
                    'options': match.group(4)
                }
    return None


def get_filesystem_usage(mount_point: str) -> Optional[Dict[str, str]]:
    """Get filesystem usage statistics"""
    exit_code, stdout, _ = run_command(f"df -h {mount_point}")
    if exit_code != 0:
        return None
    
    lines = stdout.strip().split('\n')
    if len(lines) < 2:
        return None
    
    # Parse df output
    parts = lines[1].split()
    if len(parts) >= 6:
        return {
            'filesystem': parts[0],
            'size': parts[1],
            'used': parts[2],
            'available': parts[3],
            'use_percent': parts[4],
            'mounted_on': parts[5]
        }
    return None


def check_lvm_volume(device: str) -> bool:
    """Check if device is an LVM logical volume"""
    exit_code, stdout, _ = run_command("lvs --noheadings -o lv_path")
    if exit_code != 0:
        return False
    
    return device in stdout


def validate_mount_options(options: str, required_options: List[str]) -> bool:
    """Check if mount has required options"""
    option_list = options.split(',')
    return all(opt in option_list for opt in required_options)


def main(args: List[str]) -> None:
    """Main validation logic"""
    if len(args) < 1:
        validate_fail("Mount point argument required")
    
    mount_point = args[0]
    expected_fstype = args[1] if len(args) > 1 else None
    expected_device = args[2] if len(args) > 2 else None
    
    # Check if mount point exists
    if not os.path.exists(mount_point):
        validate_fail(f"Mount point {mount_point} does not exist")
    
    print(f"✓ Mount point {mount_point} exists")
    
    # Check if mount point is a directory
    if not os.path.isdir(mount_point):
        validate_fail(f"Mount point {mount_point} is not a directory")
    
    # Get mount information
    mount_info = get_mount_info(mount_point)
    if mount_info is None:
        validate_fail(f"Mount point {mount_point} is not mounted")
    
    print(f"✓ Mount point is mounted")
    print(f"  Device: {mount_info['device']}")
    print(f"  Filesystem: {mount_info['fstype']}")
    print(f"  Options: {mount_info['options']}")
    
    # Check filesystem type if specified
    if expected_fstype:
        if mount_info['fstype'] != expected_fstype:
            validate_fail(
                f"Expected filesystem type {expected_fstype} but found {mount_info['fstype']}"
            )
        print(f"✓ Filesystem type {expected_fstype} matches expected")
    
    # Check device if specified
    if expected_device:
        if mount_info['device'] != expected_device:
            validate_fail(
                f"Expected device {expected_device} but found {mount_info['device']}"
            )
        print(f"✓ Device {expected_device} matches expected")
    
    # Get filesystem usage
    usage = get_filesystem_usage(mount_point)
    if usage:
        print(f"✓ Filesystem usage:")
        print(f"  Size: {usage['size']}")
        print(f"  Used: {usage['used']}")
        print(f"  Available: {usage['available']}")
        print(f"  Use: {usage['use_percent']}")
    
    # Check if it's an LVM volume
    if check_lvm_volume(mount_info['device']):
        print(f"✓ Device is an LVM logical volume")
    
    # Check mount point permissions
    stat_info = os.stat(mount_point)
    perms = oct(stat_info.st_mode)[-3:]
    print(f"✓ Mount point permissions: {perms}")
    
    # Verify mount point is writable (if not read-only)
    if 'ro' not in mount_info['options']:
        test_file = os.path.join(mount_point, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✓ Mount point is writable")
        except Exception as e:
            validate_fail(f"Mount point is not writable: {e}")
    
    validate_pass(f"All checks passed for mount point {mount_point}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
