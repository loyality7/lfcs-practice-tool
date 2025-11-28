"""
System Prerequisites Check Module
Validates that required system dependencies are installed and configured
"""

import sys
import subprocess
import shutil
import os
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PrerequisiteCheck:
    """Result of a prerequisite check"""
    name: str
    installed: bool
    version: Optional[str] = None
    message: str = ""
    install_instructions: str = ""


class SystemChecker:
    """
    Checks system prerequisites for LFCS Practice Tool
    
    Validates:
    - Docker installation and daemon status
    - Python version
    - Required Python packages
    - System permissions
    """
    
    def __init__(self):
        self.checks: List[PrerequisiteCheck] = []
    
    def check_all(self) -> bool:
        """
        Run all prerequisite checks
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("\n" + "=" * 70)
        print("SYSTEM PREREQUISITES CHECK")
        print("=" * 70 + "\n")
        
        # Run all checks
        self.check_python_version()
        self.check_docker_installed()
        self.check_docker_running()
        self.check_docker_permissions()
        
        # Display results
        all_passed = True
        for check in self.checks:
            status = "✓" if check.installed else "✗"
            version_info = f" ({check.version})" if check.version else ""
            print(f"{status} {check.name}{version_info}")
            
            if not check.installed:
                all_passed = False
                if check.message:
                    print(f"  ⚠ {check.message}")
                if check.install_instructions:
                    print(f"  → {check.install_instructions}")
                print()
        
        print("=" * 70)
        
        if all_passed:
            print("✓ All prerequisites satisfied!\n")
        else:
            print("✗ Some prerequisites are missing. Please install them and try again.\n")
        
        return all_passed
    
    def check_python_version(self) -> PrerequisiteCheck:
        """Check if Python version is 3.9 or higher"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 9:
            check = PrerequisiteCheck(
                name="Python 3.9+",
                installed=True,
                version=version_str,
                message="Python version is compatible"
            )
        else:
            check = PrerequisiteCheck(
                name="Python 3.9+",
                installed=False,
                version=version_str,
                message=f"Python {version_str} is too old. Python 3.9 or higher is required.",
                install_instructions="Visit https://www.python.org/downloads/ to upgrade Python"
            )
        
        self.checks.append(check)
        return check
    
    def check_docker_installed(self) -> PrerequisiteCheck:
        """Check if Docker is installed"""
        docker_path = shutil.which("docker")
        
        if docker_path:
            # Try to get Docker version
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.strip().replace("Docker version ", "").split(",")[0]
                
                check = PrerequisiteCheck(
                    name="Docker",
                    installed=True,
                    version=version,
                    message="Docker is installed"
                )
            except Exception as e:
                check = PrerequisiteCheck(
                    name="Docker",
                    installed=True,
                    version="unknown",
                    message=f"Docker is installed but version check failed: {e}"
                )
        else:
            check = PrerequisiteCheck(
                name="Docker",
                installed=False,
                message="Docker is not installed",
                install_instructions=self._get_docker_install_instructions()
            )
        
        self.checks.append(check)
        return check
    
    def check_docker_running(self) -> PrerequisiteCheck:
        """Check if Docker daemon is running and attempt to start it"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                check = PrerequisiteCheck(
                    name="Docker Daemon",
                    installed=True,
                    message="Docker daemon is running"
                )
            else:
                # Try to start Docker daemon
                print("  → Docker daemon is not running. Attempting to start it...")
                start_result = self._start_docker_daemon()
                
                if start_result:
                    check = PrerequisiteCheck(
                        name="Docker Daemon",
                        installed=True,
                        message="Docker daemon started successfully"
                    )
                else:
                    check = PrerequisiteCheck(
                        name="Docker Daemon",
                        installed=False,
                        message="Docker daemon is not running and could not be started automatically",
                        install_instructions="Start Docker daemon manually: sudo systemctl start docker"
                    )
        except FileNotFoundError:
            check = PrerequisiteCheck(
                name="Docker Daemon",
                installed=False,
                message="Cannot check Docker daemon (Docker not installed)",
                install_instructions="Install Docker first"
            )
        except subprocess.TimeoutExpired:
            check = PrerequisiteCheck(
                name="Docker Daemon",
                installed=False,
                message="Docker daemon check timed out",
                install_instructions="Check if Docker daemon is responsive: docker info"
            )
        except Exception as e:
            check = PrerequisiteCheck(
                name="Docker Daemon",
                installed=False,
                message=f"Error checking Docker daemon: {e}",
                install_instructions="Try: sudo systemctl status docker"
            )
        
        self.checks.append(check)
        return check
    
    def check_docker_permissions(self) -> PrerequisiteCheck:
        """Check if user has permissions to use Docker and attempt to fix"""
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                check = PrerequisiteCheck(
                    name="Docker Permissions",
                    installed=True,
                    message="User has Docker permissions"
                )
            elif "permission denied" in result.stderr.lower():
                # Try to fix permissions
                print("  → User does not have Docker permissions. Attempting to fix...")
                fix_result = self._fix_docker_permissions()
                
                if fix_result:
                    check = PrerequisiteCheck(
                        name="Docker Permissions",
                        installed=True,
                        message="Docker permissions fixed successfully"
                    )
                else:
                    check = PrerequisiteCheck(
                        name="Docker Permissions",
                        installed=False,
                        message="User does not have permission to access Docker",
                        install_instructions=(
                            "Add user to docker group: sudo usermod -aG docker $USER\n"
                            "  Then log out and log back in, or run: newgrp docker"
                        )
                    )
            else:
                check = PrerequisiteCheck(
                    name="Docker Permissions",
                    installed=False,
                    message=f"Cannot access Docker: {result.stderr.strip()}",
                    install_instructions="Check Docker daemon status and permissions"
                )
        except FileNotFoundError:
            check = PrerequisiteCheck(
                name="Docker Permissions",
                installed=False,
                message="Cannot check permissions (Docker not installed)",
                install_instructions="Install Docker first"
            )
        except Exception as e:
            check = PrerequisiteCheck(
                name="Docker Permissions",
                installed=False,
                message=f"Error checking Docker permissions: {e}",
                install_instructions="Try running: docker ps"
            )
        
        self.checks.append(check)
        return check
    
    def _start_docker_daemon(self) -> bool:
        """
        Attempt to start Docker daemon
        
        Returns:
            True if Docker daemon was started successfully, False otherwise
        """
        # Check if we can use sudo without password
        if not self._can_sudo_nopasswd():
            print("  ⚠ Cannot start Docker daemon automatically (requires sudo)")
            return False
        
        try:
            # Try systemctl first (most common on Linux)
            result = subprocess.run(
                ["sudo", "-n", "systemctl", "start", "docker"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Wait a moment for Docker to start
                import time
                time.sleep(2)
                
                # Verify Docker is now running
                verify = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if verify.returncode == 0:
                    print("  ✓ Docker daemon started successfully")
                    return True
            
            # Try service command as fallback
            result = subprocess.run(
                ["sudo", "-n", "service", "docker", "start"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import time
                time.sleep(2)
                
                verify = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if verify.returncode == 0:
                    print("  ✓ Docker daemon started successfully")
                    return True
            
            return False
            
        except subprocess.TimeoutExpired:
            print("  ✗ Timeout while starting Docker daemon")
            return False
        except Exception as e:
            print(f"  ✗ Could not start Docker daemon: {e}")
            return False
    
    def _fix_docker_permissions(self) -> bool:
        """
        Attempt to fix Docker permissions by adding user to docker group
        
        Returns:
            True if permissions were fixed, False otherwise
        """
        # Check if we can use sudo without password
        if not self._can_sudo_nopasswd():
            print("  ⚠ Cannot fix Docker permissions automatically (requires sudo)")
            return False
        
        try:
            username = os.environ.get('USER') or os.environ.get('USERNAME')
            if not username:
                print("  ✗ Could not determine username")
                return False
            
            # Try to add user to docker group
            result = subprocess.run(
                ["sudo", "-n", "usermod", "-aG", "docker", username],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  ✓ Added user '{username}' to docker group")
                print("  ⚠ You may need to log out and log back in for changes to take effect")
                
                # Try to apply group changes without logout using newgrp
                # Note: This won't work in the current process, but we can try
                try:
                    subprocess.run(
                        ["newgrp", "docker"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                except Exception:
                    pass
                
                # Verify permissions
                verify = subprocess.run(
                    ["docker", "ps"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if verify.returncode == 0:
                    print("  ✓ Docker permissions verified")
                    return True
                else:
                    print("  ⚠ Group added but permissions not yet active. Please log out and log back in.")
                    return False
            else:
                print(f"  ✗ Could not add user to docker group: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ✗ Timeout while fixing Docker permissions")
            return False
        except Exception as e:
            print(f"  ✗ Could not fix Docker permissions: {e}")
            return False
    
    def _can_sudo_nopasswd(self) -> bool:
        """
        Check if user can run sudo without password
        
        Returns:
            True if sudo works without password, False otherwise
        """
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_docker_install_instructions(self) -> str:
        """Get Docker installation instructions based on OS"""
        system = sys.platform
        
        if system == "linux":
            # Try to detect Linux distribution
            if os.path.exists("/etc/os-release"):
                try:
                    with open("/etc/os-release", "r") as f:
                        content = f.read().lower()
                        
                        if "ubuntu" in content or "debian" in content:
                            return (
                                "Install Docker on Ubuntu/Debian:\n"
                                "  sudo apt-get update\n"
                                "  sudo apt-get install -y docker.io\n"
                                "  sudo systemctl start docker\n"
                                "  sudo systemctl enable docker\n"
                                "  Or visit: https://docs.docker.com/engine/install/ubuntu/"
                            )
                        elif "centos" in content or "rhel" in content or "fedora" in content:
                            return (
                                "Install Docker on CentOS/RHEL/Fedora:\n"
                                "  sudo yum install -y docker\n"
                                "  sudo systemctl start docker\n"
                                "  sudo systemctl enable docker\n"
                                "  Or visit: https://docs.docker.com/engine/install/centos/"
                            )
                        elif "arch" in content:
                            return (
                                "Install Docker on Arch Linux:\n"
                                "  sudo pacman -S docker\n"
                                "  sudo systemctl start docker\n"
                                "  sudo systemctl enable docker"
                            )
                except Exception:
                    pass
            
            return (
                "Install Docker on Linux:\n"
                "  Visit: https://docs.docker.com/engine/install/\n"
                "  Select your distribution and follow the instructions"
            )
        
        elif system == "darwin":
            return (
                "Install Docker on macOS:\n"
                "  Download Docker Desktop from: https://docs.docker.com/desktop/install/mac-install/\n"
                "  Or use Homebrew: brew install --cask docker"
            )
        
        elif system == "win32":
            return (
                "Install Docker on Windows:\n"
                "  Download Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/"
            )
        
        else:
            return (
                "Install Docker:\n"
                "  Visit: https://docs.docker.com/get-docker/"
            )


def check_prerequisites(skip_check: bool = False, auto_fix: bool = True) -> bool:
    """
    Check system prerequisites and optionally fix them
    
    Args:
        skip_check: If True, skip the check (for testing or when Docker is optional)
        auto_fix: If True, offer to install missing dependencies
    
    Returns:
        True if all prerequisites are met or check is skipped, False otherwise
    """
    if skip_check:
        return True
    
    checker = SystemChecker()
    all_ok = checker.check_all()
    
    if not all_ok and auto_fix:
        print("\n" + "=" * 70)
        print("AUTOMATIC SETUP")
        print("=" * 70 + "\n")
        
        # Check what's missing
        missing_docker = not any(c.installed for c in checker.checks if c.name == "Docker")
        docker_not_running = not any(c.installed for c in checker.checks if c.name == "Docker Daemon")
        permission_issue = not any(c.installed for c in checker.checks if c.name == "Docker Permissions")
        
        if missing_docker:
            print("Docker is not installed on your system.")
            try:
                response = input("Would you like to install Docker now? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nInput cancelled.")
                response = 'n'
            
            if response == 'y':
                print("\nAttempting to install Docker...")
                if install_docker():
                    print("✓ Docker installed successfully!")
                    # Re-check
                    checker = SystemChecker()
                    all_ok = checker.check_all()
                    if all_ok:
                        return True
                else:
                    print("✗ Failed to install Docker automatically.")
                    print("Please install Docker manually using the instructions above.")
            else:
                print("\nDocker installation skipped by user.")
                print("Note: You'll need Docker to run practice scenarios.")
                print("See installation instructions above.")
        
        if docker_not_running and not missing_docker:
            print("\n📋 Docker is installed but the daemon is not running.")
            print("\nTo start Docker, please run:")
            print("  sudo systemctl start docker")
            print("\nOr enable it to start on boot:")
            print("  sudo systemctl enable --now docker")
            
            try:
                response = input("\nHave you started Docker? Press Enter to re-check, or 'n' to skip: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping Docker check.")
                response = 'n'
            
            if response != 'n':
                print("\nRe-checking Docker status...")
                # Re-check
                checker = SystemChecker()
                all_ok = checker.check_all()
                if all_ok:
                    print("\n✓ All prerequisites are now satisfied!")
                    return True
                else:
                    print("\n⚠ Docker still not running. Please check the status:")
                    print("  sudo systemctl status docker")
        
        if permission_issue and not missing_docker:
            print("\n📋 You don't have permission to access Docker.")
            print("\nTo fix this, add your user to the docker group:")
            print("  sudo usermod -aG docker $USER")
            print("\nThen log out and log back in, or run:")
            print("  newgrp docker")
            
            try:
                response = input("\nHave you fixed permissions? Press Enter to re-check, or 'n' to skip: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping permission check.")
                response = 'n'
            
            if response != 'n':
                print("\nRe-checking Docker permissions...")
                # Re-check
                checker = SystemChecker()
                all_ok = checker.check_all()
                if all_ok:
                    print("\n✓ All prerequisites are now satisfied!")
                    return True
                else:
                    print("\n⚠ Permissions still not fixed.")
                    print("Make sure you ran: newgrp docker")
                    print("Or log out and log back in for changes to take effect.")
        
        # Final check - if we still have issues, return False
        print("\n" + "=" * 70)
        if not all_ok:
            print("⚠ Setup incomplete. Please resolve the issues above to continue.")
            print("=" * 70 + "\n")
        else:
            print("✓ All issues resolved! You can now use LFCS Practice Tool.")
            print("=" * 70 + "\n")
    
    return all_ok


def install_docker() -> bool:
    """
    Attempt to install Docker based on the OS
    
    Returns:
        True if installation succeeded, False otherwise
    """
    system = sys.platform
    
    try:
        if system == "linux":
            # Detect Linux distribution
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    
                    if "ubuntu" in content or "debian" in content:
                        print("Detected Ubuntu/Debian system...")
                        commands = [
                            ["sudo", "apt-get", "update"],
                            ["sudo", "apt-get", "install", "-y", "docker.io"],
                            ["sudo", "systemctl", "start", "docker"],
                            ["sudo", "systemctl", "enable", "docker"]
                        ]
                        
                        for cmd in commands:
                            print(f"Running: {' '.join(cmd)}")
                            result = subprocess.run(cmd, capture_output=True, text=True)
                            if result.returncode != 0:
                                print(f"Error: {result.stderr}")
                                return False
                        
                        return True
                    
                    elif "centos" in content or "rhel" in content or "fedora" in content:
                        print("Detected CentOS/RHEL/Fedora system...")
                        commands = [
                            ["sudo", "yum", "install", "-y", "docker"],
                            ["sudo", "systemctl", "start", "docker"],
                            ["sudo", "systemctl", "enable", "docker"]
                        ]
                        
                        for cmd in commands:
                            print(f"Running: {' '.join(cmd)}")
                            result = subprocess.run(cmd, capture_output=True, text=True)
                            if result.returncode != 0:
                                print(f"Error: {result.stderr}")
                                return False
                        
                        return True
        
        elif system == "darwin":
            print("On macOS, Docker Desktop needs to be installed manually.")
            print("Opening Docker Desktop download page...")
            subprocess.run(["open", "https://docs.docker.com/desktop/install/mac-install/"])
            return False
        
        elif system == "win32":
            print("On Windows, Docker Desktop needs to be installed manually.")
            print("Opening Docker Desktop download page...")
            subprocess.run(["start", "https://docs.docker.com/desktop/install/windows-install/"], shell=True)
            return False
        
        print(f"Automatic installation not supported on {system}")
        return False
        
    except Exception as e:
        print(f"Error during installation: {e}")
        return False


def start_docker() -> bool:
    """
    Attempt to start Docker daemon
    
    Returns:
        True if start succeeded, False otherwise
    """
    try:
        print("\nStarting Docker daemon...")
        print("⚠ You may be prompted for your sudo password.")
        
        # Run sudo command without capturing output so user can see password prompt
        result = subprocess.run(
            ["sudo", "systemctl", "start", "docker"],
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Docker daemon start command executed")
            
            # Wait a moment for daemon to fully start
            import time
            print("Waiting for Docker daemon to initialize...")
            time.sleep(3)
            
            # Verify it's running
            print("Verifying Docker daemon status...")
            verify = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if verify.returncode == 0:
                print("✓ Docker daemon is now running!")
                return True
            else:
                print("✗ Docker daemon started but not responding yet")
                print("It may take a few more seconds. Try running your command again.")
                return False
        else:
            print(f"✗ Failed to start Docker daemon")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Docker start command timed out")
        return False
    except KeyboardInterrupt:
        print("\n✗ Docker start cancelled by user")
        return False
    except Exception as e:
        print(f"✗ Error starting Docker: {e}")
        return False


def fix_docker_permissions() -> bool:
    """
    Attempt to fix Docker permissions by adding user to docker group
    
    Returns:
        True if fix succeeded, False otherwise
    """
    try:
        import getpass
        username = getpass.getuser()
        
        print(f"\nAdding user '{username}' to docker group...")
        print("⚠ You may be prompted for your sudo password.")
        
        # Run sudo command without capturing output so user can see password prompt
        result = subprocess.run(
            ["sudo", "usermod", "-aG", "docker", username],
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✓ User '{username}' added to docker group")
            print("\n⚠ IMPORTANT: You need to log out and log back in for this to take effect.")
            print("Or run: newgrp docker")
            print("\nAfter logging out/in, run your command again.")
            return True
        else:
            print(f"✗ Failed to add user to docker group")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Permission fix command timed out")
        return False
    except KeyboardInterrupt:
        print("\n✗ Permission fix cancelled by user")
        return False
    except Exception as e:
        print(f"✗ Error fixing permissions: {e}")
        return False
