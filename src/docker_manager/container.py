"""
Docker Container Manager
Handles container lifecycle for isolated practice environments
"""

import docker
from docker.errors import DockerException, ImageNotFound, APIError, NotFound
from typing import Dict, Optional, Tuple, Any
import logging
import os
import tarfile
import io
from dataclasses import dataclass

from ..utils.config import DockerConfig
from ..core.models import Scenario
from ..utils.error_handler import ErrorHandler, ErrorContext, handle_docker_error


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of command execution in container"""
    exit_code: int
    output: str
    error: Optional[str] = None


class DockerManager:
    """
    Manages Docker container lifecycle for practice sessions
    
    Responsibilities:
    - Create and configure containers with appropriate base images
    - Execute commands in containers
    - Copy files to/from containers
    - Clean up containers and resources
    - Handle Docker daemon errors
    """
    
    def __init__(self, config: DockerConfig):
        """
        Initialize Docker Manager
        
        Args:
            config: Docker configuration
            
        Raises:
            DockerException: If Docker daemon is not available
        """
        self.config = config
        self.error_handler = ErrorHandler()
        
        # Check if Docker daemon is available
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker daemon connection established")
        except DockerException as e:
            logger.error(f"Docker daemon not available: {e}")
            
            # Use error handler for better error reporting
            context = ErrorContext(user_action="initialize_docker_manager")
            response = handle_docker_error(e, context, self.error_handler)
            
            # Print user-friendly error message
            print(self.error_handler.format_error_for_user(response))
            
            raise DockerException(
                "Docker is not installed or not running. "
                "Please install Docker and ensure the daemon is running. "
                "Visit https://docs.docker.com/get-docker/ for installation instructions."
            ) from e
    
    def create_container(self, distribution: str, scenario: Scenario) -> docker.models.containers.Container:
        """
        Create and start a container for a practice session
        
        Args:
            distribution: Linux distribution (ubuntu, centos, rocky)
            scenario: Scenario to set up the container for
            
        Returns:
            Docker container object
            
        Raises:
            ImageNotFound: If the base image is not available
            APIError: If container creation fails
        """
        # Determine image to use
        image_name = self._get_image_name(distribution)
        
        # Ensure image is available
        try:
            self.client.images.get(image_name)
            logger.info(f"Using existing image: {image_name}")
        except ImageNotFound as e:
            logger.warning(f"Image {image_name} not found, building automatically...")
            
            # Import image builder
            from .image_builder import DockerImageBuilder
            
            # Build the image automatically
            builder = DockerImageBuilder(self.client)
            
            print(f"\n⚠️  Docker image '{image_name}' not found.")
            print("Building it automatically (this is a one-time setup)...\n")
            
            success = builder.build_image(distribution, show_progress=True)
            
            if not success:
                # Use error handler for better error reporting
                context = ErrorContext(
                    scenario_id=scenario.id,
                    user_action="create_container",
                    category=scenario.category,
                    difficulty=scenario.difficulty,
                    additional_info={'image_name': image_name, 'distribution': distribution}
                )
                response = handle_docker_error(e, context, self.error_handler)
                print(self.error_handler.format_error_for_user(response))
                
                raise ImageNotFound(
                    f"Failed to build image '{image_name}'. "
                    f"Please check Docker daemon and try again."
                ) from e
        
        # Create container configuration
        container_config = {
            'image': image_name,
            'detach': True,
            'tty': True,
            'stdin_open': True,
            'network_mode': self.config.network_mode,
            'privileged': self.config.privileged,
            'remove': False,  # We'll remove manually for cleanup control
            'name': f"lfcs-practice-{scenario.id}-{os.getpid()}",
            # Required for systemd to work in containers
            'volumes': {
                '/sys/fs/cgroup': {'bind': '/sys/fs/cgroup', 'mode': 'ro'},
                # Mount control directory if provided
                **({self.config.control_dir: {'bind': '/opt/lfcs/control', 'mode': 'rw'}} 
                   if hasattr(self.config, 'control_dir') and self.config.control_dir else {})
            },
            'tmpfs': {'/run': '', '/run/lock': ''},
            'cap_add': ['SYS_ADMIN'],
        }
        
        try:
            # Create and start container
            container = self.client.containers.run(**container_config)
            logger.info(f"Created container {container.short_id} for scenario {scenario.id}")
            
            # Run setup commands if specified
            if scenario.setup_commands:
                logger.info(f"Running {len(scenario.setup_commands)} setup commands")
                for cmd in scenario.setup_commands:
                    result = self.execute_command(container, cmd)
                    if result.exit_code != 0:
                        logger.warning(f"Setup command failed: {cmd} (exit code: {result.exit_code})")
                        logger.warning(f"Output: {result.output}")
            
            return container
            
        except APIError as e:
            logger.error(f"Failed to create container: {e}")
            
            # Use error handler for better error reporting
            context = ErrorContext(
                scenario_id=scenario.id,
                user_action="create_container",
                category=scenario.category,
                difficulty=scenario.difficulty,
                additional_info={'image_name': image_name, 'distribution': distribution}
            )
            response = handle_docker_error(e, context, self.error_handler)
            print(self.error_handler.format_error_for_user(response))
            
            raise APIError(
                f"Failed to create container: {e}. "
                "Check Docker daemon logs and ensure sufficient resources are available."
            ) from e
    
    def execute_command(self, container: docker.models.containers.Container, 
                       command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Execute a command in the container
        
        Args:
            container: Docker container object
            command: Command to execute
            timeout: Optional timeout in seconds
            
        Returns:
            ExecutionResult with exit code and output
            
        Raises:
            APIError: If command execution fails
        """
        try:
            # Refresh container state
            container.reload()
            
            # Check if container is running
            if container.status != 'running':
                raise APIError(f"Container {container.short_id} is not running (status: {container.status})")
            
            # Execute command
            logger.debug(f"Executing command in {container.short_id}: {command}")
            exec_result = container.exec_run(
                command,
                demux=True,  # Separate stdout and stderr
                tty=False,
            )
            
            exit_code = exec_result.exit_code
            
            # Handle demuxed output (stdout, stderr)
            stdout, stderr = exec_result.output
            
            output = ""
            error = None
            
            if stdout:
                output = stdout.decode('utf-8', errors='replace')
            
            if stderr:
                error = stderr.decode('utf-8', errors='replace')
            
            logger.debug(f"Command exit code: {exit_code}")
            
            return ExecutionResult(
                exit_code=exit_code,
                output=output,
                error=error
            )
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            
            # Use error handler for better error reporting
            context = ErrorContext(
                container_id=container.short_id,
                user_action="execute_command",
                additional_info={'command': command}
            )
            response = handle_docker_error(e, context, self.error_handler)
            
            raise APIError(f"Failed to execute command in container: {e}") from e
    
    def copy_to_container(self, container: docker.models.containers.Container, 
                         src: str, dest: str) -> None:
        """
        Copy a file or directory to the container
        
        Args:
            container: Docker container object
            src: Source path on host
            dest: Destination path in container
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            APIError: If copy operation fails
        """
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source path does not exist: {src}")
        
        try:
            # Create tar archive in memory
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                tar.add(src, arcname=os.path.basename(src))
            
            tar_stream.seek(0)
            
            # Copy to container
            container.put_archive(dest, tar_stream)
            logger.info(f"Copied {src} to {container.short_id}:{dest}")
            
        except Exception as e:
            logger.error(f"Failed to copy file to container: {e}")
            raise APIError(f"Failed to copy file to container: {e}") from e
    
    def destroy_container(self, container: docker.models.containers.Container) -> None:
        """
        Stop and remove a container, cleaning up all resources
        
        Args:
            container: Docker container object
        """
        try:
            container_id = container.short_id
            
            # Stop container if running
            try:
                container.reload()
                if container.status == 'running':
                    logger.info(f"Stopping container {container_id}")
                    container.stop(timeout=10)
            except NotFound:
                logger.warning(f"Container {container_id} already removed")
                return
            except Exception as e:
                logger.warning(f"Error stopping container {container_id}: {e}")
            
            # Remove container
            try:
                logger.info(f"Removing container {container_id}")
                container.remove(force=True)
                logger.info(f"Container {container_id} removed successfully")
            except NotFound:
                logger.warning(f"Container {container_id} already removed")
            except Exception as e:
                logger.error(f"Error removing container {container_id}: {e}")
                # Try force remove as last resort
                try:
                    container.remove(force=True, v=True)
                except Exception as e2:
                    logger.error(f"Force remove also failed for {container_id}: {e2}")
                    
        except Exception as e:
            logger.error(f"Error during container cleanup: {e}")
    
    def get_container_shell(self, container: docker.models.containers.Container) -> str:
        """
        Get the command to attach to container shell
        
        Args:
            container: Docker container object
            
        Returns:
            Shell command string
        """
        return f"docker exec -it {container.name} /bin/bash"
    
    def _get_image_name(self, distribution: str) -> str:
        """
        Get the full image name for a distribution
        
        Args:
            distribution: Distribution name (ubuntu, centos, rocky)
            
        Returns:
            Full image name
        """
        # Use custom images if available, otherwise fall back to standard images
        if distribution in self.config.images:
            return self.config.images[distribution]
        
        # Fallback to base image prefix
        return f"{self.config.base_image_prefix}-{distribution}:latest"
    
    def check_docker_available(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Docker daemon is available and responsive
        
        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            self.client.ping()
            return True, None
        except DockerException as e:
            error_msg = (
                "Docker daemon is not available. "
                "Please ensure Docker is installed and running.\n"
                "Installation instructions: https://docs.docker.com/get-docker/\n"
                f"Error: {e}"
            )
            return False, error_msg
