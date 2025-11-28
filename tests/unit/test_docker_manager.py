"""
Property-based tests for Docker Manager
Tests container isolation and multi-distribution compatibility
"""

import pytest
import docker
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from docker.errors import DockerException, ImageNotFound
import os
import tempfile
import time

from src.docker_manager.container import DockerManager, ExecutionResult
from src.utils.config import DockerConfig
from src.core.models import Scenario, ValidationRules, CommandCheck


# Check if Docker is available
def is_docker_available():
    """Check if Docker daemon is available"""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except:
        return False


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker daemon not available"
)


# Fixtures
@pytest.fixture
def docker_config():
    """Create a test Docker configuration"""
    return DockerConfig(
        base_image_prefix="lfcs-practice",
        default_distribution="ubuntu",
        container_timeout=300,
        privileged=True,
        network_mode="bridge",
        cleanup_on_exit=True,
        images={
            "ubuntu": "ubuntu:22.04",
            "centos": "centos:stream9",
            "rocky": "rockylinux:9"
        }
    )


@pytest.fixture
def docker_manager(docker_config):
    """Create a Docker manager instance"""
    return DockerManager(docker_config)


@pytest.fixture
def simple_scenario():
    """Create a simple test scenario"""
    return Scenario(
        id="test-scenario-001",
        category="essential_commands",
        difficulty="easy",
        task="Test task",
        validation=ValidationRules(checks=[
            CommandCheck(command="echo test", expected_output="test")
        ]),
        points=10,
        distribution=None,
        setup_commands=[],
        hints=[],
        time_limit=None,
        tags=[]
    )


# Strategy generators for property-based testing
@st.composite
def scenario_generator(draw):
    """Generate random but valid scenarios"""
    categories = ['networking', 'storage', 'users_groups', 
                  'operations_deployment', 'essential_commands']
    difficulties = ['easy', 'medium', 'hard']
    distributions = [None, 'ubuntu', 'centos', 'rocky']
    
    scenario_id = f"test-{draw(st.integers(min_value=1, max_value=10000))}"
    category = draw(st.sampled_from(categories))
    difficulty = draw(st.sampled_from(difficulties))
    distribution = draw(st.sampled_from(distributions))
    
    # Generate simple setup commands
    setup_commands = draw(st.lists(
        st.sampled_from([
            "echo 'setup'",
            "mkdir -p /tmp/test",
            "touch /tmp/testfile"
        ]),
        max_size=3
    ))
    
    return Scenario(
        id=scenario_id,
        category=category,
        difficulty=difficulty,
        task=f"Test task for {category}",
        validation=ValidationRules(checks=[
            CommandCheck(command="echo test", expected_output="test")
        ]),
        points=draw(st.integers(min_value=10, max_value=100)),
        distribution=distribution,
        setup_commands=setup_commands,
        hints=[],
        time_limit=None,
        tags=[]
    )


@st.composite
def file_path_generator(draw):
    """Generate valid file paths for testing"""
    filename = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    ))
    return f"/tmp/test_{filename}.txt"


# Feature: lfcs-practice-environment, Property 3: Container isolation
@settings(
    max_examples=100,
    deadline=60000,  # 60 seconds per test
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(
    scenario1=scenario_generator(),
    scenario2=scenario_generator(),
    test_file_path=file_path_generator()
)
def test_container_isolation_property(docker_manager, scenario1, scenario2, test_file_path):
    """
    Property 3: Container isolation
    
    For any practice session, when a container is created and destroyed,
    no artifacts from that session should persist on the host system or
    affect subsequent sessions.
    
    Validates: Requirements 2.1, 2.4
    """
    # Use ubuntu for faster testing
    distribution = "ubuntu"
    
    container1 = None
    container2 = None
    
    try:
        # Create first container and create a file
        container1 = docker_manager.create_container(distribution, scenario1)
        
        # Create a unique file in the first container
        test_content = f"test_content_{scenario1.id}"
        result1 = docker_manager.execute_command(
            container1,
            f"echo '{test_content}' > {test_file_path}"
        )
        assert result1.exit_code == 0, "Failed to create test file in container1"
        
        # Verify file exists in container1
        result2 = docker_manager.execute_command(
            container1,
            f"cat {test_file_path}"
        )
        assert result2.exit_code == 0, "File should exist in container1"
        assert test_content in result2.output, "File content should match in container1"
        
        # Destroy first container
        docker_manager.destroy_container(container1)
        container1 = None
        
        # Verify file doesn't exist on host
        assert not os.path.exists(test_file_path), \
            "File from container should not exist on host system"
        
        # Create second container
        container2 = docker_manager.create_container(distribution, scenario2)
        
        # Verify file from first container doesn't exist in second container
        result3 = docker_manager.execute_command(
            container2,
            f"cat {test_file_path}"
        )
        # File should not exist (exit code should be non-zero)
        assert result3.exit_code != 0, \
            "File from first container should not exist in second container"
        
        # Verify second container has clean state
        result4 = docker_manager.execute_command(
            container2,
            "ls /tmp | wc -l"
        )
        assert result4.exit_code == 0, "Should be able to list /tmp in container2"
        
    finally:
        # Cleanup
        if container1:
            try:
                docker_manager.destroy_container(container1)
            except:
                pass
        if container2:
            try:
                docker_manager.destroy_container(container2)
            except:
                pass


# Feature: lfcs-practice-environment, Property 11: Multi-distribution compatibility
@settings(
    max_examples=100,
    deadline=60000,  # 60 seconds per test
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(
    scenario=scenario_generator(),
    distribution=st.sampled_from(['ubuntu', 'centos', 'rocky'])
)
def test_multi_distribution_compatibility_property(docker_manager, scenario, distribution):
    """
    Property 11: Multi-distribution compatibility
    
    For any scenario marked as distribution-agnostic (no specific distribution field),
    the scenario should execute successfully on Ubuntu, CentOS, and Rocky Linux containers.
    
    Validates: Requirements 8.1, 8.4
    """
    # Make scenario distribution-agnostic
    scenario.distribution = None
    
    container = None
    
    try:
        # Create container with specified distribution
        container = docker_manager.create_container(distribution, scenario)
        
        # Verify container was created successfully
        assert container is not None, f"Container should be created for {distribution}"
        
        # Verify container is running
        container.reload()
        assert container.status == 'running', \
            f"Container should be running on {distribution}"
        
        # Execute basic commands that should work on all distributions
        basic_commands = [
            "echo 'test'",
            "pwd",
            "whoami",
            "ls /",
        ]
        
        for cmd in basic_commands:
            result = docker_manager.execute_command(container, cmd)
            assert result.exit_code == 0, \
                f"Command '{cmd}' should succeed on {distribution} (exit code: {result.exit_code})"
            assert result.output is not None, \
                f"Command '{cmd}' should produce output on {distribution}"
        
        # Verify we can create files
        test_file = f"/tmp/test_{scenario.id}.txt"
        result = docker_manager.execute_command(
            container,
            f"echo 'test content' > {test_file} && cat {test_file}"
        )
        assert result.exit_code == 0, \
            f"Should be able to create and read files on {distribution}"
        assert "test content" in result.output, \
            f"File operations should work correctly on {distribution}"
        
    finally:
        # Cleanup
        if container:
            try:
                docker_manager.destroy_container(container)
            except:
                pass


# Unit tests for specific functionality
class TestDockerManagerUnit:
    """Unit tests for Docker Manager"""
    
    def test_docker_manager_initialization(self, docker_config):
        """Test Docker manager can be initialized"""
        manager = DockerManager(docker_config)
        assert manager is not None
        assert manager.client is not None
    
    def test_docker_available_check(self, docker_manager):
        """Test Docker availability check"""
        is_available, error = docker_manager.check_docker_available()
        assert is_available is True
        assert error is None
    
    def test_create_and_destroy_container(self, docker_manager, simple_scenario):
        """Test basic container lifecycle"""
        container = None
        try:
            # Create container
            container = docker_manager.create_container("ubuntu", simple_scenario)
            assert container is not None
            
            # Verify container is running
            container.reload()
            assert container.status == 'running'
            
            # Destroy container
            docker_manager.destroy_container(container)
            
            # Verify container is removed
            with pytest.raises(docker.errors.NotFound):
                container.reload()
                
        except Exception as e:
            if container:
                try:
                    docker_manager.destroy_container(container)
                except:
                    pass
            raise
    
    def test_execute_command(self, docker_manager, simple_scenario):
        """Test command execution in container"""
        container = None
        try:
            container = docker_manager.create_container("ubuntu", simple_scenario)
            
            # Execute simple command
            result = docker_manager.execute_command(container, "echo 'hello world'")
            assert result.exit_code == 0
            assert "hello world" in result.output
            
        finally:
            if container:
                docker_manager.destroy_container(container)
    
    def test_copy_to_container(self, docker_manager, simple_scenario):
        """Test copying files to container"""
        container = None
        temp_file = None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write("test content")
                temp_file = f.name
            
            container = docker_manager.create_container("ubuntu", simple_scenario)
            
            # Copy file to container
            docker_manager.copy_to_container(container, temp_file, "/tmp/")
            
            # Verify file exists in container
            filename = os.path.basename(temp_file)
            result = docker_manager.execute_command(
                container,
                f"cat /tmp/{filename}"
            )
            assert result.exit_code == 0
            assert "test content" in result.output
            
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if container:
                docker_manager.destroy_container(container)
    
    def test_get_container_shell_command(self, docker_manager, simple_scenario):
        """Test getting shell command for container"""
        container = None
        try:
            container = docker_manager.create_container("ubuntu", simple_scenario)
            shell_cmd = docker_manager.get_container_shell(container)
            
            assert "docker exec -it" in shell_cmd
            assert container.name in shell_cmd
            assert "/bin/bash" in shell_cmd
            
        finally:
            if container:
                docker_manager.destroy_container(container)
