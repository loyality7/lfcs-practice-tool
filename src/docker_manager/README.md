# Docker Manager

The Docker Manager component handles the lifecycle of Docker containers used for isolated practice environments in the LFCS Practice Tool.

## Features

- **Container Creation**: Creates isolated Docker containers from base images
- **Multi-Distribution Support**: Supports Ubuntu, CentOS, and Rocky Linux
- **Command Execution**: Executes commands inside containers with output capture
- **File Transfer**: Copies files to containers for validation scripts
- **Resource Cleanup**: Properly destroys containers and cleans up resources
- **Error Handling**: Detects Docker daemon issues and provides helpful error messages

## Usage

### Basic Example

```python
from src.docker_manager.container import DockerManager
from src.utils.config import DockerConfig
from src.core.models import Scenario, ValidationRules

# Create configuration
config = DockerConfig(
    default_distribution="ubuntu",
    privileged=True,
    container_timeout=3600
)

# Initialize manager
manager = DockerManager(config)

# Check Docker availability
is_available, error = manager.check_docker_available()
if not is_available:
    print(f"Docker not available: {error}")
    exit(1)

# Create a scenario
scenario = Scenario(
    id="test-001",
    category="essential_commands",
    difficulty="easy",
    task="Create a user",
    validation=ValidationRules(checks=[]),
    points=10,
    setup_commands=["apt-get update"]
)

# Create container
container = manager.create_container("ubuntu", scenario)

# Execute commands
result = manager.execute_command(container, "whoami")
print(f"Output: {result.output}")
print(f"Exit code: {result.exit_code}")

# Copy files to container
manager.copy_to_container(container, "/path/to/script.sh", "/tmp/")

# Cleanup
manager.destroy_container(container)
```

## API Reference

### DockerManager

#### `__init__(config: DockerConfig)`

Initialize the Docker Manager with configuration.

**Raises:**
- `DockerException`: If Docker daemon is not available

#### `create_container(distribution: str, scenario: Scenario) -> Container`

Create and start a container for a practice session.

**Parameters:**
- `distribution`: Linux distribution (ubuntu, centos, rocky)
- `scenario`: Scenario to set up the container for

**Returns:**
- Docker container object

**Raises:**
- `ImageNotFound`: If the base image is not available
- `APIError`: If container creation fails

#### `execute_command(container: Container, command: str, timeout: Optional[int] = None) -> ExecutionResult`

Execute a command in the container.

**Parameters:**
- `container`: Docker container object
- `command`: Command to execute
- `timeout`: Optional timeout in seconds

**Returns:**
- `ExecutionResult` with exit code, output, and error

**Raises:**
- `APIError`: If command execution fails

#### `copy_to_container(container: Container, src: str, dest: str) -> None`

Copy a file or directory to the container.

**Parameters:**
- `container`: Docker container object
- `src`: Source path on host
- `dest`: Destination path in container

**Raises:**
- `FileNotFoundError`: If source file doesn't exist
- `APIError`: If copy operation fails

#### `destroy_container(container: Container) -> None`

Stop and remove a container, cleaning up all resources.

**Parameters:**
- `container`: Docker container object

#### `get_container_shell(container: Container) -> str`

Get the command to attach to container shell.

**Parameters:**
- `container`: Docker container object

**Returns:**
- Shell command string (e.g., "docker exec -it container_name /bin/bash")

#### `check_docker_available() -> Tuple[bool, Optional[str]]`

Check if Docker daemon is available and responsive.

**Returns:**
- Tuple of (is_available, error_message)

## Configuration

The Docker Manager uses `DockerConfig` for configuration:

```python
@dataclass
class DockerConfig:
    base_image_prefix: str = "lfcs-practice"
    default_distribution: str = "ubuntu"
    container_timeout: int = 3600  # 1 hour
    privileged: bool = True
    network_mode: str = "bridge"
    cleanup_on_exit: bool = True
    images: Dict[str, str] = field(default_factory=lambda: {
        "ubuntu": "ubuntu:22.04",
        "centos": "centos:stream9",
        "rocky": "rockylinux:9"
    })
```

## Error Handling

The Docker Manager provides comprehensive error handling:

1. **Docker Daemon Not Available**: Detects when Docker is not installed or not running
2. **Image Not Found**: Provides instructions to build or pull base images
3. **Container Creation Failure**: Logs details and suggests troubleshooting steps
4. **Command Execution Errors**: Captures stderr and provides detailed error messages
5. **Cleanup Failures**: Attempts force removal as fallback

## Testing

### Unit Tests

Run unit tests with pytest:

```bash
pytest tests/unit/test_docker_manager.py -v
```

### Property-Based Tests

The Docker Manager includes property-based tests using Hypothesis:

- **Property 3: Container Isolation** - Verifies containers don't share state
- **Property 11: Multi-Distribution Compatibility** - Verifies scenarios work across distributions

### Manual Testing

Run the manual test script when Docker is available:

```bash
python tests/manual_docker_test.py
```

## Requirements

- Docker Engine 20.10+
- Python 3.9+
- docker-py 6.0+

## Base Images

The Docker Manager expects base images to be available:

- `lfcs-practice-ubuntu:latest` or `ubuntu:22.04`
- `lfcs-practice-centos:latest` or `centos:stream9`
- `lfcs-practice-rocky:latest` or `rockylinux:9`

Build base images:

```bash
cd docker/base_images
./build_all.sh
```

## Security Considerations

- Containers run in privileged mode by default (required for system administration tasks)
- Network isolation can be configured via `network_mode`
- Containers are automatically cleaned up after use
- Resource limits should be configured in production environments

## Troubleshooting

### Docker daemon not available

```
Error: Docker is not installed or not running
```

**Solution**: Install Docker and start the daemon:
- Linux: `sudo systemctl start docker`
- macOS/Windows: Start Docker Desktop

### Permission denied

```
Error: permission denied while trying to connect to the Docker daemon socket
```

**Solution**: Add user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Image not found

```
Error: Base image 'lfcs-practice-ubuntu:latest' not found
```

**Solution**: Build base images:
```bash
cd docker/base_images
./build_all.sh
```
