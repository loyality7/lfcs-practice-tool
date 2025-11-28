# LFCS Practice Tool - Developer Guide

Guide for developers who want to contribute to the project or create custom scenarios.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Creating Scenarios](#creating-scenarios)
4. [Creating Learning Modules](#creating-learning-modules)
5. [Writing Tests](#writing-tests)
6. [Code Style](#code-style)
7. [Contributing](#contributing)

## Development Setup

### Prerequisites

- Python 3.9+
- Docker 20.10+
- Git
- Text editor or IDE

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/loyality7/lfcs-practice-tool.git
cd lfcs-practice-tool

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,test,ai]"

# Build Docker images
cd docker/base_images
./build_all.sh
cd ../..

# Run tests to verify setup
pytest
```

### Development Tools

Install recommended tools:

```bash
# Code formatting
pip install black flake8

# Type checking
pip install mypy

# Testing
pip install pytest pytest-cov hypothesis

# Pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Project Structure

```
lfcs-practice-tool/
├── src/                          # Source code
│   ├── cli/                      # Command-line interface
│   │   └── main_cli.py          # CLI implementation
│   ├── core/                     # Core functionality
│   │   ├── engine.py            # Main orchestration engine
│   │   ├── scenario_loader.py  # Scenario loading and parsing
│   │   ├── models.py            # Data models
│   │   ├── interfaces.py        # Abstract interfaces
│   │   └── context_generator.py # Random context generation
│   ├── docker_manager/           # Docker management
│   │   ├── container.py         # Container lifecycle
│   │   └── environment.py       # Environment abstraction
│   ├── validation/               # Validation system
│   │   ├── validator.py         # Main validator
│   │   └── strategies/          # Validation strategies
│   │       ├── command.py       # Command validation
│   │       ├── file.py          # File validation
│   │       └── service.py       # Service validation
│   ├── learn/                    # Learning system
│   │   ├── module_loader.py    # Module loading
│   │   ├── interactive_shell.py # Interactive exercises
│   │   └── models.py            # Learning models
│   ├── utils/                    # Utilities
│   │   ├── config.py            # Configuration management
│   │   ├── db_manager.py        # Database and scoring
│   │   ├── error_handler.py    # Error handling
│   │   ├── system_check.py     # System prerequisites
│   │   ├── colors.py            # Terminal colors
│   │   └── banner.py            # UI components
│   └── main.py                   # Entry point
├── scenarios/                    # Practice scenarios
│   ├── essential_commands/
│   ├── networking/
│   ├── operations_deployment/
│   ├── storage/
│   └── users_groups/
├── learn_modules/                # Learning modules
│   ├── 01_beginner/
│   ├── 02_intermediate/
│   ├── 03_advanced/
│   └── 04_expert/
├── docker/                       # Docker configuration
│   ├── base_images/             # Base image Dockerfiles
│   │   ├── ubuntu/
│   │   ├── centos/
│   │   └── rocky/
│   └── validation_scripts/      # Custom validation scripts
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test fixtures
├── config/                       # Configuration files
├── database/                     # Database schema
├── docs/                         # Documentation
└── logs/                         # Log files
```

## Creating Scenarios

### Scenario File Format

Scenarios are defined in YAML files with the following structure:

```yaml
id: category_difficulty_description_01
category: networking
difficulty: medium
distribution: null  # null for all, or ubuntu/centos/rocky
task: |
  Configure the network interface eth0 with the following settings:
  - IP address: 192.168.1.100
  - Netmask: 255.255.255.0
  - Gateway: 192.168.1.1
  - DNS: 8.8.8.8, 8.8.4.4
  
  Ensure the configuration persists across reboots.

setup_commands:
  - "ip link set eth0 down"
  - "ip addr flush dev eth0"

validation:
  checks:
    - type: command
      command: "ip addr show eth0"
      expected_pattern: "192\\.168\\.1\\.100"
      description: "IP address configured correctly"
    
    - type: file
      path: "/etc/network/interfaces"
      should_exist: true
      content_contains: "192.168.1.100"
      description: "Configuration file updated"
    
    - type: command
      command: "ping -c 1 192.168.1.1"
      expected_exit_code: 0
      description: "Gateway reachable"

points: 150
hints:
  - "Use ip command or edit /etc/network/interfaces"
  - "Don't forget to bring the interface up after configuration"
  - "Test connectivity with ping before submitting"
time_limit: 600  # seconds (optional)
```

### Validation Types

#### 1. Command Validation

Validates by running a command and checking output:

```yaml
- type: command
  command: "systemctl is-active nginx"
  expected_output: "active"
  expected_exit_code: 0
  description: "Nginx service is running"
```

With regex pattern:

```yaml
- type: command
  command: "cat /etc/passwd"
  expected_pattern: "^alice:.*:2000:"
  description: "User alice exists with UID 2000"
```

#### 2. File Validation

Validates file existence, permissions, ownership, and content:

```yaml
- type: file
  path: "/etc/nginx/nginx.conf"
  should_exist: true
  permissions: "0644"
  owner: "root"
  group: "root"
  content_contains: "server_name example.com"
  description: "Nginx configuration file correct"
```

#### 3. Service Validation

Validates systemd service status:

```yaml
- type: service
  service_name: "nginx"
  should_be_running: true
  should_be_enabled: true
  description: "Nginx service configured correctly"
```

#### 4. Custom Script Validation

For complex validation logic:

```yaml
- type: custom
  script: "validate_network_config.sh"
  description: "Network configuration validated"
```

Place custom scripts in `docker/validation_scripts/`.

### Context Variables

Use Jinja2 templates for randomized scenarios:

```yaml
task: |
  Create a user named {{ random_user }} with UID {{ random_port }}.
  Set the home directory to /home/{{ random_user }}.

validation:
  checks:
    - type: command
      command: "id {{ random_user }}"
      expected_pattern: "uid={{ random_port }}"
      description: "User created with correct UID"
```

Available variables:
- `{{ random_file }}` - Random filename
- `{{ random_dir }}` - Random directory name
- `{{ random_user }}` - Random username
- `{{ random_group }}` - Random group name
- `{{ random_ip }}` - Random IP address
- `{{ random_port }}` - Random port number
- `{{ random_text }}` - Random text
- `{{ uuid }}` - UUID

### Scenario Best Practices

1. **Clear Task Description**
   - Be specific about requirements
   - Include all necessary details
   - Use proper formatting

2. **Comprehensive Validation**
   - Test multiple aspects
   - Include positive and negative checks
   - Provide descriptive check names

3. **Progressive Hints**
   - Start general, get more specific
   - Don't give away the complete solution
   - Guide thinking, not just commands

4. **Appropriate Points**
   - Easy: 50-100 points
   - Medium: 100-150 points
   - Hard: 150-200 points

5. **Setup Commands**
   - Prepare the environment
   - Create necessary files/users
   - Set initial state

### Testing Scenarios

```bash
# Test your scenario
lfcs start --category your_category --difficulty your_difficulty

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('scenarios/path/to/scenario.yaml'))"

# Run validation manually
cd docker/base_images
docker run -it lfcs-practice-ubuntu:latest /bin/bash
# Test commands manually
```

### Scenario Naming Convention

- **File name**: `descriptive_name_01.yaml`
- **Scenario ID**: `category_difficulty_description_01`
- Use lowercase with underscores
- Number scenarios sequentially

### Example Scenarios

#### Easy Scenario

```yaml
id: storage_easy_create_directory_01
category: storage
difficulty: easy
task: |
  Create a directory named /data/backups with the following properties:
  - Owner: root
  - Group: root
  - Permissions: 755

validation:
  checks:
    - type: file
      path: "/data/backups"
      should_exist: true
      permissions: "0755"
      owner: "root"
      group: "root"
      description: "Directory created with correct properties"

points: 50
hints:
  - "Use mkdir command to create directories"
  - "Use chmod to set permissions"
  - "Use chown to set ownership"
```

#### Medium Scenario

```yaml
id: networking_medium_static_ip_01
category: networking
difficulty: medium
task: |
  Configure a static IP address for interface eth0:
  - IP: 10.0.2.100/24
  - Gateway: 10.0.2.1
  - DNS: 8.8.8.8
  
  Make the configuration persistent.

setup_commands:
  - "ip addr flush dev eth0"

validation:
  checks:
    - type: command
      command: "ip addr show eth0"
      expected_pattern: "10\\.0\\.2\\.100"
      description: "IP address configured"
    
    - type: command
      command: "ip route show"
      expected_pattern: "default via 10\\.0\\.2\\.1"
      description: "Gateway configured"
    
    - type: file
      path: "/etc/network/interfaces"
      should_exist: true
      content_contains: "10.0.2.100"
      description: "Configuration persisted"

points: 120
hints:
  - "Edit /etc/network/interfaces for persistent configuration"
  - "Use ip command for immediate configuration"
  - "Restart networking service to apply changes"
```

#### Hard Scenario

```yaml
id: operations_hard_systemd_service_01
category: operations_deployment
difficulty: hard
task: |
  Create a systemd service named 'backup-service' that:
  - Runs /usr/local/bin/backup.sh every hour
  - Starts automatically on boot
  - Restarts on failure
  - Runs as user 'backup'
  
  Create the backup user and script as needed.

setup_commands:
  - "rm -f /etc/systemd/system/backup-service.service"
  - "userdel -r backup 2>/dev/null || true"

validation:
  checks:
    - type: file
      path: "/etc/systemd/system/backup-service.service"
      should_exist: true
      description: "Service file exists"
    
    - type: service
      service_name: "backup-service"
      should_be_enabled: true
      description: "Service enabled"
    
    - type: command
      command: "systemctl show backup-service -p User"
      expected_output: "User=backup"
      description: "Service runs as backup user"
    
    - type: command
      command: "id backup"
      expected_exit_code: 0
      description: "Backup user exists"

points: 200
hints:
  - "Create service file in /etc/systemd/system/"
  - "Use systemctl enable to start on boot"
  - "Set Restart=on-failure in service file"
  - "Create backup user with useradd"
```

## Creating Learning Modules

### Module File Format

Learning modules are YAML files with lessons and exercises:

```yaml
id: "01_beginner/01_linux_basics"
level: "beginner"
title: "Linux Basics and File System"
description: "Introduction to Linux and the file system hierarchy"
estimated_time: 30
prerequisites: []

lessons:
  - id: "lesson_01"
    title: "Understanding the Linux File System"
    estimated_time: 10
    notes: |
      Linux uses a hierarchical file system starting from root (/).
      
      Key directories:
      - /home - User home directories
      - /etc - Configuration files
      - /var - Variable data (logs, caches)
      - /usr - User programs and data
      - /tmp - Temporary files
    
    exercises:
      - id: "ex_01"
        type: "command"
        description: "List the contents of the root directory"
        command: "ls"
        expected_pattern: "home.*etc.*var"
        points: 10
        hints:
          - "Use ls command to list directory contents"
          - "Try: ls /"
      
      - id: "ex_02"
        type: "question"
        question: "Which directory contains user home directories?"
        options:
          - "/home"
          - "/usr"
          - "/var"
          - "/etc"
        correct_answer: "/home"
        points: 10
      
      - id: "ex_03"
        type: "task"
        description: "Navigate to your home directory"
        validation:
          type: "command"
          command: "pwd"
          expected_pattern: "/root"
        points: 10
        hints:
          - "Use cd command to change directory"
          - "Try: cd ~"
```

### Exercise Types

#### Command Exercise

User must execute a specific command:

```yaml
- id: "ex_01"
  type: "command"
  description: "Create a directory named 'test'"
  command: "mkdir"
  expected_output: ""  # No output expected
  points: 10
  hints:
    - "Use mkdir command"
    - "Syntax: mkdir <directory_name>"
```

#### Question Exercise

Multiple choice question:

```yaml
- id: "ex_02"
  type: "question"
  question: "What command shows current directory?"
  options:
    - "pwd"
    - "cd"
    - "ls"
    - "dir"
  correct_answer: "pwd"
  points: 10
```

#### Task Exercise

Free-form task with validation:

```yaml
- id: "ex_03"
  type: "task"
  description: "Create a file named test.txt in /tmp"
  validation:
    type: "file"
    path: "/tmp/test.txt"
  points: 15
  hints:
    - "Use touch command to create files"
    - "Try: touch /tmp/test.txt"
```

## Writing Tests

### Unit Tests

Create unit tests in `tests/unit/`:

```python
import pytest
from src.core.scenario_loader import ScenarioLoader

def test_scenario_loader_loads_all_scenarios():
    """Test that scenario loader loads all scenarios"""
    loader = ScenarioLoader("scenarios")
    scenarios = loader.load_all()
    
    assert len(scenarios) > 0
    assert "networking" in scenarios
    assert "storage" in scenarios

def test_scenario_validation():
    """Test scenario structure validation"""
    loader = ScenarioLoader("scenarios")
    scenario = loader.get_by_id("storage_easy_create_directory_01")
    
    assert scenario is not None
    assert scenario.category == "storage"
    assert scenario.difficulty == "easy"
    assert len(scenario.validation.checks) > 0
```

### Property-Based Tests

Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st
from src.core.scenario_loader import ScenarioLoader

# Feature: lfcs-practice-environment, Property 1: Scenario loading completeness
@given(st.sampled_from(['networking', 'storage', 'users_groups']))
def test_all_scenarios_in_category_load_successfully(category):
    """For any category, all scenarios should load without errors"""
    loader = ScenarioLoader("scenarios")
    scenarios = loader.list_scenarios(category=category)
    
    assert len(scenarios) > 0
    for scenario in scenarios:
        assert scenario.category == category
        assert scenario.id is not None
        assert len(scenario.validation.checks) > 0
```

### Integration Tests

Test complete workflows:

```python
def test_full_practice_session():
    """Test complete practice session workflow"""
    from src.core.engine import Engine
    from src.utils.config import load_config
    
    config = load_config()
    engine = Engine(config)
    
    # Start session
    result = engine.start_session(
        category="storage",
        difficulty="easy",
        scenario_id="storage_easy_create_directory_01"
    )
    
    assert result is not None
    assert result.scenario.id == "storage_easy_create_directory_01"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_scenario_loader.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run property-based tests only
pytest -k "property"

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_scenario_loader.py::test_scenario_loader_loads_all_scenarios
```

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

- **Line length**: 100 characters
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Grouped (standard library, third-party, local)

### Formatting

Use Black for automatic formatting:

```bash
# Format all code
black src/ tests/

# Check without modifying
black --check src/ tests/
```

### Linting

Use flake8 for linting:

```bash
# Lint code
flake8 src/ tests/

# With specific rules
flake8 --max-line-length=100 --ignore=E203,W503 src/
```

### Type Hints

Use type hints for function signatures:

```python
from typing import List, Optional, Dict

def load_scenarios(path: str, category: Optional[str] = None) -> List[Scenario]:
    """
    Load scenarios from path
    
    Args:
        path: Path to scenarios directory
        category: Optional category filter
    
    Returns:
        List of Scenario objects
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_score(max_score: int, checks_passed: int, 
                   checks_total: int) -> int:
    """
    Calculate score based on validation results
    
    Args:
        max_score: Maximum possible score
        checks_passed: Number of checks that passed
        checks_total: Total number of checks
    
    Returns:
        Calculated score as integer
    
    Raises:
        ValueError: If checks_total is zero
    """
    if checks_total == 0:
        raise ValueError("checks_total cannot be zero")
    
    return int((checks_passed / checks_total) * max_score)
```

## Contributing

### Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

4. **Run tests**:
   ```bash
   pytest
   black src/ tests/
   flake8 src/ tests/
   ```

5. **Commit your changes**:
   ```bash
   git commit -m "feat: add new networking scenario"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

### Commit Message Format

Use conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Build process or auxiliary tool changes

**Examples**:
```
feat(scenarios): add advanced networking scenarios

fix(docker): handle container cleanup errors gracefully

docs(readme): update installation instructions

test(validator): add property-based tests for validation
```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what and why
- **Tests**: Include tests for new features
- **Documentation**: Update relevant docs
- **Changelog**: Note breaking changes

### Code Review Process

1. Automated checks run (tests, linting, coverage)
2. Manual review by maintainers
3. Feedback and requested changes
4. Approval and merge

---

For more information, see:
- [User Guide](../user_guide/USER_GUIDE.md)
- [Architecture Documentation](../architecture/ARCHITECTURE.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
