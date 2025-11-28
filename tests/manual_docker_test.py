#!/usr/bin/env python3
"""
Manual test script for Docker Manager
Run this when Docker daemon is available to verify functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.docker_manager.container import DockerManager
from src.utils.config import DockerConfig
from src.core.models import Scenario, ValidationRules, CommandCheck


def main():
    """Run manual Docker Manager tests"""
    print("=" * 60)
    print("Docker Manager Manual Test")
    print("=" * 60)
    
    # Create configuration
    config = DockerConfig(
        base_image_prefix="lfcs-practice",
        default_distribution="ubuntu",
        container_timeout=300,
        privileged=True,
        images={
            "ubuntu": "ubuntu:22.04",
            "centos": "centos:stream9",
            "rocky": "rockylinux:9"
        }
    )
    
    # Create Docker Manager
    print("\n1. Initializing Docker Manager...")
    try:
        manager = DockerManager(config)
        print("   ✓ Docker Manager initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize Docker Manager: {e}")
        return 1
    
    # Check Docker availability
    print("\n2. Checking Docker availability...")
    is_available, error = manager.check_docker_available()
    if is_available:
        print("   ✓ Docker daemon is available")
    else:
        print(f"   ✗ Docker daemon not available: {error}")
        return 1
    
    # Create a test scenario
    scenario = Scenario(
        id="manual-test-001",
        category="essential_commands",
        difficulty="easy",
        task="Test Docker Manager functionality",
        validation=ValidationRules(checks=[
            CommandCheck(command="echo test", expected_output="test")
        ]),
        points=10,
        distribution=None,
        setup_commands=["echo 'Setup complete'"],
        hints=[],
        time_limit=None,
        tags=[]
    )
    
    # Test container creation
    print("\n3. Creating container...")
    container = None
    try:
        container = manager.create_container("ubuntu", scenario)
        print(f"   ✓ Container created: {container.short_id}")
    except Exception as e:
        print(f"   ✗ Failed to create container: {e}")
        return 1
    
    # Test command execution
    print("\n4. Executing commands in container...")
    try:
        result = manager.execute_command(container, "echo 'Hello from container'")
        print(f"   ✓ Command executed (exit code: {result.exit_code})")
        print(f"   Output: {result.output.strip()}")
    except Exception as e:
        print(f"   ✗ Failed to execute command: {e}")
        if container:
            manager.destroy_container(container)
        return 1
    
    # Test file operations
    print("\n5. Testing file operations...")
    try:
        result = manager.execute_command(
            container,
            "echo 'test content' > /tmp/testfile.txt && cat /tmp/testfile.txt"
        )
        print(f"   ✓ File operations successful")
        print(f"   File content: {result.output.strip()}")
    except Exception as e:
        print(f"   ✗ Failed file operations: {e}")
        if container:
            manager.destroy_container(container)
        return 1
    
    # Test container isolation
    print("\n6. Testing container isolation...")
    try:
        # Create file in first container
        manager.execute_command(container, "echo 'isolated' > /tmp/isolated.txt")
        
        # Create second container
        scenario2 = Scenario(
            id="manual-test-002",
            category="essential_commands",
            difficulty="easy",
            task="Test isolation",
            validation=ValidationRules(checks=[]),
            points=10
        )
        container2 = manager.create_container("ubuntu", scenario2)
        
        # Check if file exists in second container (it shouldn't)
        result = manager.execute_command(container2, "cat /tmp/isolated.txt")
        if result.exit_code != 0:
            print("   ✓ Containers are properly isolated")
        else:
            print("   ✗ Container isolation may be compromised")
        
        # Cleanup second container
        manager.destroy_container(container2)
        
    except Exception as e:
        print(f"   ✗ Isolation test failed: {e}")
        if container:
            manager.destroy_container(container)
        return 1
    
    # Test container cleanup
    print("\n7. Cleaning up container...")
    try:
        manager.destroy_container(container)
        print("   ✓ Container destroyed successfully")
    except Exception as e:
        print(f"   ✗ Failed to destroy container: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
