# LFCS Practice Tool - Architecture Documentation

Technical architecture and design decisions for the LFCS Practice Tool.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Extensibility](#extensibility)

## System Overview

The LFCS Practice Tool is a modular, CLI-based application that provides an interactive learning environment for Linux system administration. The system uses Docker containers for isolation, YAML files for scenario definitions, and SQLite for progress tracking.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer (main_cli.py)                 │
│  - Argument parsing (argparse)                              │
│  - Command routing (start, stats, list, reset, learn)      │
│  - User interaction and output formatting                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Core Engine (engine.py)                    │
│  - Session orchestration                                    │
│  - Component coordination                                   │
│  - Workflow management                                      │
│  - Error handling                                           │
└─────┬──────────┬──────────┬──────────┬──────────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────────────┐
│ Scenario │ │ Docker  │ │Validator │ │ Scorer/Storage │
│ Loader   │ │ Manager │ │          │ │                │
└──────────┘ └─────────┘ └──────────┘ └────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────────────┐
│  YAML    │ │ Docker  │ │Validation│ │   SQLite DB    │
│  Files   │ │ Daemon  │ │ Scripts  │ │                │
└──────────┘ └─────────┘ └──────────┘ └────────────────┘

Optional Components:
┌─────────────────────────────────────────────────────────────┐
│                    Learning System                          │
│  - Module loader                                            │
│  - Interactive shell                                        │
│  - Exercise execution                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AI Module (Optional)                     │
│  - Scenario generation                                      │
│  - Intelligent validation                                   │
│  - Hint generation                                          │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:
- **CLI**: User interaction only
- **Engine**: Orchestration only
- **Scenario Loader**: Scenario management only
- **Docker Manager**: Container lifecycle only
- **Validator**: Validation logic only
- **Scorer**: Scoring and persistence only

### 2. Modularity

Components are loosely coupled and can be:
- Developed independently
- Tested in isolation
- Replaced or extended without affecting others

### 3. Extensibility

System supports extension through:
- Plugin-based validation strategies
- YAML-based scenario definitions
- Configuration-driven behavior
- Abstract interfaces for key components

### 4. Reliability

System ensures reliability through:
- Comprehensive error handling
- Automatic recovery mechanisms
- Transaction-based database operations
- Container cleanup on failure

### 5. Testability

Design supports testing through:
- Dependency injection
- Abstract interfaces
- Property-based testing
- Integration test support

## Component Architecture

### CLI Layer

**Responsibility**: User interaction and command routing

**Key Classes**:
- `CLI`: Main CLI class with command handlers

**Design**:
- Uses argparse for command parsing
- Routes commands to engine methods
- Formats output for terminal display
- Handles user input validation

**Interactions**:
- Calls engine methods
- Displays results to user
- Handles keyboard interrupts

### Core Engine

**Responsibility**: Orchestrate practice sessions and coordinate components

**Key Classes**:
- `Engine`: Main orchestration engine
- `SessionResult`: Session result data

**Design**:
- Implements session workflow
- Coordinates all components
- Manages session state
- Handles errors and cleanup

**Session Workflow**:
1. Load scenario
2. Create container
3. Display task
4. Wait for user
5. Run validation
6. Calculate score
7. Persist results
8. Clean up container
9. Return results

### Scenario Loader

**Responsibility**: Load and manage scenario definitions

**Key Classes**:
- `ScenarioLoader`: Loads scenarios from YAML
- `Scenario`: Scenario data model
- `ContextGenerator`: Generates random context

**Design**:
- Lazy loading of scenarios
- Caching for performance
- YAML validation
- Jinja2 template rendering

**Features**:
- Category filtering
- Difficulty filtering
- Distribution filtering
- Random scenario selection
- Scenario validation

### Docker Manager

**Responsibility**: Manage Docker container lifecycle

**Key Classes**:
- `DockerManager`: Container management
- `ExecutionResult`: Command execution result

**Design**:
- Uses docker-py SDK
- Handles container creation, execution, cleanup
- Manages container configuration
- Implements error recovery

**Features**:
- Multi-distribution support
- Privileged containers for system tasks
- Volume mounting for validation scripts
- Network configuration
- Resource limits

### Validator

**Responsibility**: Validate task completion

**Key Classes**:
- `Validator`: Main validator
- `ValidationResult`: Validation result
- `CheckResult`: Individual check result

**Design**:
- Strategy pattern for validation types
- Pluggable validation strategies
- Detailed feedback generation

**Validation Strategies**:
- `CommandStrategy`: Command-based validation
- `FileStrategy`: File-based validation
- `ServiceStrategy`: Service-based validation

### Scorer and Storage

**Responsibility**: Calculate scores and persist progress

**Key Classes**:
- `Scorer`: Scoring and database management
- `Statistics`: User statistics
- `CategoryStats`: Category-specific stats
- `DifficultyStats`: Difficulty-specific stats

**Design**:
- SQLite for local storage
- Transaction-based operations
- Retry logic for database locks
- Comprehensive statistics calculation

**Features**:
- Score calculation with difficulty multipliers
- Progress tracking
- Streak calculation
- Mastery percentage calculation
- Personalized recommendations
- Achievement system

### Learning System

**Responsibility**: Interactive learning modules

**Key Classes**:
- `ModuleLoader`: Loads learning modules
- `InteractiveShell`: Executes exercises
- `LearningModule`, `Lesson`, `Exercise`: Data models

**Design**:
- YAML-based module definitions
- Interactive exercise execution
- Progressive hint system
- State tracking for shell commands

**Exercise Types**:
- Command exercises
- Question exercises
- Task exercises

### Error Handler

**Responsibility**: Centralized error handling

**Key Classes**:
- `ErrorHandler`: Main error handler
- `ErrorResponse`: Error response data
- `ErrorContext`: Error context information

**Design**:
- Categorizes errors
- Determines severity
- Generates user-friendly messages
- Suggests recovery actions
- Logs with full context

**Error Categories**:
- Docker errors
- Scenario errors
- Validation errors
- Database errors
- Configuration errors
- System errors

## Data Flow

### Practice Session Flow

```
User Input
    ↓
CLI (parse command)
    ↓
Engine.start_session()
    ↓
ScenarioLoader.get_scenario()
    ↓
DockerManager.create_container()
    ↓
Display task to user
    ↓
User works in container
    ↓
Validator.validate()
    ↓
Scorer.calculate_score()
    ↓
Scorer.record_attempt()
    ↓
DockerManager.destroy_container()
    ↓
Return SessionResult
    ↓
CLI (display results)
    ↓
User sees feedback
```

### Validation Flow

```
Validator.validate()
    ↓
For each check in scenario:
    ↓
    Determine check type
    ↓
    Select strategy
    ↓
    Strategy.validate()
        ↓
        Execute in container
        ↓
        Check result
        ↓
        Return CheckResult
    ↓
    Collect results
    ↓
Generate feedback
    ↓
Return ValidationResult
```

### Statistics Flow

```
User requests stats
    ↓
CLI.cmd_stats()
    ↓
Engine.get_statistics()
    ↓
Scorer.get_statistics()
    ↓
Query database
    ↓
Calculate aggregates
    ↓
Calculate mastery
    ↓
Generate recommendations
    ↓
Return Statistics
    ↓
CLI (format and display)
```

## Technology Stack

### Core Technologies

- **Python 3.9+**: Main programming language
- **Docker**: Container runtime
- **SQLite**: Local database
- **YAML**: Configuration and scenario format

### Python Libraries

**Core Dependencies**:
- `docker`: Docker SDK for Python
- `PyYAML`: YAML parsing
- `python-dotenv`: Environment variable management
- `tabulate`: Table formatting
- `colorama`: Terminal colors
- `Jinja2`: Template rendering

**Development Dependencies**:
- `pytest`: Testing framework
- `hypothesis`: Property-based testing
- `pytest-cov`: Code coverage
- `black`: Code formatting
- `flake8`: Linting
- `mypy`: Type checking

**Optional Dependencies**:
- `openai`: OpenAI API client
- `anthropic`: Anthropic API client

### Infrastructure

- **Docker Images**: Ubuntu, CentOS, Rocky Linux
- **File System**: YAML files for scenarios and modules
- **Database**: SQLite for progress tracking
- **Logs**: File-based logging

## Design Patterns

### 1. Strategy Pattern

Used in validation system:

```python
class ValidatorStrategy(ABC):
    @abstractmethod
    def validate(self, environment: Environment, 
                check_config: Dict) -> ValidationResult:
        pass

class CommandStrategy(ValidatorStrategy):
    def validate(self, environment, check_config):
        # Command validation logic
        pass

class FileStrategy(ValidatorStrategy):
    def validate(self, environment, check_config):
        # File validation logic
        pass
```

### 2. Factory Pattern

Used in scenario loading:

```python
class Scenario:
    @classmethod
    def from_dict(cls, data: Dict) -> 'Scenario':
        # Create scenario from dictionary
        pass
```

### 3. Singleton Pattern

Used in configuration:

```python
_config_instance = None

def load_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader().load()
    return _config_instance
```

### 4. Template Method Pattern

Used in engine workflow:

```python
class Engine:
    def start_session(self, ...):
        scenario = self._load_scenario(...)
        container = self._create_container(...)
        self._display_task(...)
        self._wait_for_user()
        result = self._validate_scenario(...)
        score = self._calculate_score(...)
        self._record_attempt(...)
        self._cleanup_container(...)
        return SessionResult(...)
```

### 5. Adapter Pattern

Used for environment abstraction:

```python
class Environment(ABC):
    @abstractmethod
    def execute_command(self, command: str) -> ExecutionResult:
        pass

class DockerEnvironment(Environment):
    def __init__(self, container):
        self.container = container
    
    def execute_command(self, command: str) -> ExecutionResult:
        # Adapt Docker container to Environment interface
        pass
```

## Security Considerations

### Container Isolation

- Containers run in isolated environments
- No access to host filesystem (except mounted volumes)
- Network isolation options
- Resource limits to prevent DoS

### Privileged Containers

- Required for system administration tasks
- Isolated from host
- Destroyed after use
- No persistent state

### Input Validation

- All user inputs validated
- YAML files validated before loading
- Command injection prevention
- Path traversal prevention

### API Keys

- Never stored in code or config files
- Environment variables only
- Not logged
- Optional feature

### Database Security

- Local SQLite database
- No network exposure
- File permissions enforced
- No sensitive data stored

## Performance Optimization

### Caching

- Scenarios cached after first load
- Docker images cached locally
- Database connections pooled

### Lazy Loading

- Scenarios loaded on demand
- Docker images pulled only when needed
- Statistics calculated on request

### Resource Management

- Containers destroyed after use
- Database connections closed properly
- File handles released
- Memory-efficient data structures

### Parallel Operations

- Multiple validation checks can run in parallel
- Background monitoring for live validation
- Async operations where appropriate

## Extensibility

### Adding New Validation Types

1. Create new strategy class
2. Implement `ValidatorStrategy` interface
3. Register in validator
4. Document in scenario guide

### Adding New Distributions

1. Create Dockerfile in `docker/base_images/`
2. Add build script
3. Update configuration
4. Test scenarios

### Adding New Categories

1. Create directory in `scenarios/`
2. Add scenarios
3. Update configuration
4. Update documentation

### Adding AI Providers

1. Implement `AIModule` interface
2. Add provider-specific logic
3. Update configuration
4. Add API key handling

### Custom Validation Scripts

1. Create script in `docker/validation_scripts/`
2. Make executable
3. Reference in scenario YAML
4. Test in container

---

For more information, see:
- [User Guide](../user_guide/USER_GUIDE.md)
- [Developer Guide](../developer_guide/DEVELOPER_GUIDE.md)
- [Design Document](.kiro/specs/lfcs-practice-environment/design.md)
