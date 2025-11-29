"""Version checking and update utilities"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# Cache file location
CACHE_DIR = Path.home() / ".lfcs"
VERSION_CACHE_FILE = CACHE_DIR / "version_check.json"
CHECK_INTERVAL = timedelta(days=1)  # Check once per day


def get_current_version() -> str:
    """Get the current installed version"""
    try:
        # Try to get version from package metadata
        from importlib.metadata import version
        return version("lfcs")
    except Exception:
        # Fallback to hardcoded version if package not installed
        return "1.1.0"


def get_latest_version_from_pypi() -> Optional[str]:
    """
    Check PyPI for the latest version
    
    Returns:
        Latest version string or None if check fails
    """
    try:
        url = "https://pypi.org/pypi/lfcs/json"
        req = urllib.request.Request(url, headers={'User-Agent': 'lfcs-practice-tool'})
        
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            return data['info']['version']
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.debug(f"Failed to check PyPI for updates: {e}")
        return None
    except Exception as e:
        logger.debug(f"Unexpected error checking for updates: {e}")
        return None


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse version string into tuple for comparison"""
    try:
        return tuple(int(x) for x in version_str.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_newer_version(current: str, latest: str) -> bool:
    """Check if latest version is newer than current"""
    return parse_version(latest) > parse_version(current)


def read_version_cache() -> Optional[dict]:
    """Read cached version check data"""
    try:
        if not VERSION_CACHE_FILE.exists():
            return None
        
        with open(VERSION_CACHE_FILE, 'r') as f:
            data = json.load(f)
            
        # Check if cache is still valid
        last_check = datetime.fromisoformat(data.get('last_check', ''))
        if datetime.now() - last_check > CHECK_INTERVAL:
            return None
            
        return data
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def write_version_cache(latest_version: str) -> None:
    """Write version check data to cache"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        data = {
            'last_check': datetime.now().isoformat(),
            'latest_version': latest_version
        }
        
        with open(VERSION_CACHE_FILE, 'w') as f:
            json.dump(data, f)
    except OSError as e:
        logger.debug(f"Failed to write version cache: {e}")


def check_for_updates(force: bool = False) -> Optional[str]:
    """
    Check if a newer version is available
    
    Args:
        force: If True, bypass cache and force fresh check
    
    Returns:
        Latest version string if update available, None otherwise
    """
    current_version = get_current_version()
    
    # Try cache first unless forced
    if not force:
        cached = read_version_cache()
        if cached:
            latest = cached.get('latest_version')
            if latest and is_newer_version(current_version, latest):
                return latest
            return None
    
    # Perform fresh check
    latest_version = get_latest_version_from_pypi()
    
    if latest_version:
        # Update cache
        write_version_cache(latest_version)
        
        # Return if update available
        if is_newer_version(current_version, latest_version):
            return latest_version
    
    return None


def get_update_command() -> str:
    """Get the appropriate update command for the current system"""
    # Check if installed via pip or pipx
    if os.path.exists(sys.prefix + '/bin/pipx') or 'pipx' in sys.prefix:
        return "pipx upgrade lfcs"
    else:
        return "pip install --upgrade lfcs"


def print_update_notification(new_version: str) -> None:
    """Print a friendly update notification"""
    from .colors import Colors, info, success, highlight, dim
    
    current = get_current_version()
    update_cmd = get_update_command()
    
    print()
    print(f"{Colors.YELLOW}╭{'─' * 68}╮{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET} {success('📦 Update Available!')} " + " " * 49 + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}" + " " * 70 + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}  {dim('Current version:')} {info(current)}" + " " * (52 - len(current)) + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}  {dim('Latest version: ')} {highlight(new_version)}" + " " * (52 - len(new_version)) + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}" + " " * 70 + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}│{Colors.RESET}  {dim('Update with:')} {success(update_cmd)}" + " " * (54 - len(update_cmd)) + f"{Colors.YELLOW}│{Colors.RESET}")
    print(f"{Colors.YELLOW}╰{'─' * 68}╯{Colors.RESET}")
    print()


def perform_update() -> int:
    """
    Perform the package update
    
    Returns:
        Exit code (0 for success)
    """
    import subprocess
    from .colors import info, success, error
    
    update_cmd = get_update_command()
    
    print(f"\n{info('Updating lfcs package...')}")
    print(f"{info(f'Running: {update_cmd}')}\n")
    
    try:
        # Run the update command
        result = subprocess.run(
            update_cmd.split(),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n{success('✓ Update completed successfully!')}")
            print(f"{info('Please restart lfcs to use the new version.')}\n")
            return 0
        else:
            print(f"\n{error('✗ Update failed.')}")
            print(f"{info('Please try manually: ')} {update_cmd}\n")
            return 1
            
    except Exception as e:
        print(f"\n{error(f'✗ Update failed: {e}')}")
        print(f"{info('Please try manually: ')} {update_cmd}\n")
        return 1
