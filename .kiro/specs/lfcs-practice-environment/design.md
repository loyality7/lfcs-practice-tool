# Design Document

## Overview

The LFCS Practice Environment is a Python-based CLI application that provides an interactive learning platform for Linux system administration. The architecture follows a modular design with clear separation of concerns: the CLI layer handles user interaction, the core layer manages business logic and orchestration, the validation layer verifies task completion, and the storage layer persists user progress. Docker containers provide isolated practice environments, while YAML files define reusable scenarios. An optional AI module enhances the experience with dynamic content generation.

The system operates in a request-response cycle: users request scenarios through the CLI, the engine loads scenario definitions, spins up Docker containers, allows users to work on tasks, validates completion, calculates scores, and persists results. This design ensures safety (isolated containers), repeatability (clean state for each session), and measurability (tracked progress over time).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer (main_cli.py)                 │
│  - Argument parsing (argparse)                              │
│  - Command routing (start, stats, list, reset)             │
│  - User interaction and output formatting                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Core Engine (engine.py)                    │
│  - Session orchestration                                    │
│  - Component coordination                                   │
│  - Workflow management                                      │
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

Optional AI Layer:
┌─────────────────────────────────────────────────────────────┐
│                    AI Module (ai/)                          │
│  - Scenario generation (scenario_generator.py)              │
│  - Intelligent validation (validator.py)                    │
│  - Hint generation                                          │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User → CLI → Engine → Scenario Loader → YAML Files
                ↓
              Docker Manager → Container Creation
                ↓
              User works in container
                ↓
              Validator → Execute checks in container
                ↓
              Scorer → Calculate points
                ↓
              Storage → Persist to database
                ↓
              CLI → Display results to user
```

## Components and Interfaces

### 1. CLI Layer (`src/cli/main_cli.py`)

**Responsibility:** User interaction, command parsing, output formatting

**Interface:**
```python
class CLI:
    def __init__(self, engine: Engine):
        """Initialize CLI with core engine"""
        
    def run(self, args: List[str]) -> int:
        """Main entry point, returns exit code"""
        
    def cmd_start(self, category: str, difficulty: str, 
                  distribution: str, ai_mode: bool) -> None:
        """Start a practice session"""
        
    def cmd_stats(self, category: Optional[str]) -> None:
        """Display user statistics"""
        
    def cmd_list(self, category: Optional[str], 
                 difficulty: Optional[str]) -> None:
        """List available scenarios"""
        
    def cmd_reset(self, confirm: bool) -> None:
        """Reset user progress"""
```

**Commands:**
- `start --category <cat> --difficulty <diff> --distribution <dist> [--ai]`
- `stats [--category <cat>]`
- `list [--category <cat>] [--difficulty <diff>]`
- `reset --confirm`

### 2. Core Engine (`src/core/engine.py`)

**Responsibility:** Orchestrate practice sessions, coordinate components

**Interface:**
```python
class Engine:
    def __init__(self, config: Config):
        """Initialize with configuration"""
        self.scenario_loader = ScenarioLoader(config.scenarios_path)
        self.docker_manager = DockerManager(config.docker_config)
        self.validator = Validator(config.validation_config)
        self.scorer = Scorer(config.database_path)
        self.ai_module = AIModule(config.ai_config) if config.ai_enabled else None
        
    def start_session(self, category: str, difficulty: str, 
                     distribution: str, ai_mode: bool) -> SessionResult:
        """Start and manage a complete practice session"""
        
    def get_statistics(self, category: Optional[str]) -> Statistics:
        """Retrieve user statistics"""
        
    def list_scenarios(self, category: Optional[str], 
                      difficulty: Optional[str]) -> List[Scenario]:
        """List available scenarios"""
```

**Session Workflow:**
1. Load or generate scenario
2. Create Docker container
3. Display task to user
4. Wait for user to complete task
5. Run validation
6. Calculate score
7. Persist results
8. Clean up container
9. Display results

### 3. Scenario Loader (`src/core/scenario_loader.py`)

**Responsibility:** Load, parse, and manage scenario definitions

**Interface:**
```python
class ScenarioLoader:
    def __init__(self, scenarios_path: str):
        """Initialize with path to scenarios directory"""
        
    def load_all(self) -> Dict[str, List[Scenario]]:
        """Load all scenarios organized by category"""
        
    def get_scenario(self, category: str, difficulty: Optional[str],
                    distribution: Optional[str]) -> Scenario:
        """Get a random scenario matching criteria"""
        
    def get_by_id(self, scenario_id: str) -> Scenario:
        """Get specific scenario by ID"""
        
    def validate_scenario(self, scenario: Dict) -> bool:
        """Validate scenario structure"""
```

**Scenario Data Model:**
```python
@dataclass
class Scenario:
    id: str
    category: str
    difficulty: str  # easy, medium, hard
    distribution: Optional[str]  # ubuntu, centos, rocky, or None for all
    task: str  # Description shown to user
    setup_commands: List[str]  # Commands to run before user starts
    validation: ValidationRules
    points: int
    hints: List[str]
    time_limit: Optional[int]  # seconds
```

### 4. Docker Manager (`src/docker_manager/container.py`)

**Responsibility:** Manage Docker container lifecycle

**Interface:**
```python
class DockerManager:
    def __init__(self, config: DockerConfig):
        """Initialize with Docker configuration"""
        self.client = docker.from_env()
        
    def create_container(self, distribution: str, 
                        scenario: Scenario) -> Container:
        """Create and start a container"""
        
    def execute_command(self, container: Container, 
                       command: str) -> ExecutionResult:
        """Execute command in container"""
        
    def copy_to_container(self, container: Container, 
                         src: str, dest: str) -> None:
        """Copy files into container"""
        
    def destroy_container(self, container: Container) -> None:
        """Stop and remove container"""
        
    def get_container_shell(self, container: Container) -> str:
        """Get command to attach to container shell"""
```

**Container Configuration:**
- Base images: `lfcs-practice-ubuntu`, `lfcs-practice-centos`, `lfcs-practice-rocky`
- Privileged mode for system administration tasks
- Volume mounts for validation scripts
- Network configuration for networking scenarios

### 5. Validator (`src/validation/validator.py`)

**Responsibility:** Verify task completion

**Interface:**
```python
class Validator:
    def __init__(self, config: ValidationConfig):
        """Initialize validator"""
        
    def validate(self, container: Container, 
                scenario: Scenario) -> ValidationResult:
        """Run all validation checks"""
        
    def validate_command(self, container: Container, 
                        check: CommandCheck) -> CheckResult:
        """Validate by running command and checking output"""
        
    def validate_file(self, container: Container, 
                     check: FileCheck) -> CheckResult:
        """Validate file existence, permissions, content"""
        
    def validate_service(self, container: Container, 
                        check: ServiceCheck) -> CheckResult:
        """Validate service status"""
        
    def validate_custom(self, container: Container, 
                       script_path: str) -> CheckResult:
        """Run custom validation script"""
```

**Validation Rules Data Model:**
```python
@dataclass
class ValidationRules:
    checks: List[Union[CommandCheck, FileCheck, ServiceCheck, CustomCheck]]
    
@dataclass
class CommandCheck:
    command: str
    expected_output: Optional[str]
    expected_exit_code: int = 0
    regex_match: Optional[str] = None
    
@dataclass
class FileCheck:
    path: str
    should_exist: bool = True
    permissions: Optional[str] = None  # e.g., "0644"
    owner: Optional[str] = None
    content_contains: Optional[str] = None
    
@dataclass
class ServiceCheck:
    service_name: str
    should_be_running: bool = True
    should_be_enabled: bool = True
```

### 6. Scorer and Storage (`src/utils/db_manager.py`)

**Responsibility:** Calculate scores and persist progress

**Interface:**
```python
class Scorer:
    def __init__(self, db_path: str):
        """Initialize with database path"""
        
    def calculate_score(self, scenario: Scenario, 
                       validation_result: ValidationResult) -> int:
        """Calculate points earned"""
        
    def record_attempt(self, scenario_id: str, score: int, 
                      passed: bool, duration: int) -> None:
        """Record attempt in database"""
        
    def get_statistics(self, category: Optional[str]) -> Statistics:
        """Get user statistics"""
        
    def get_recommendations(self) -> List[str]:
        """Get personalized recommendations based on performance"""
```

**Database Schema:**
```sql
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    duration INTEGER,  -- seconds
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    unlocked_at DATETIME
);

CREATE INDEX idx_attempts_category ON attempts(category);
CREATE INDEX idx_attempts_timestamp ON attempts(timestamp);
```

### 7. AI Module (Optional) (`src/ai/`)

**Responsibility:** Generate scenarios and provide intelligent feedback

**Interface:**
```python
class AIModule:
    def __init__(self, config: AIConfig):
        """Initialize with AI configuration (API keys, model)"""
        
    def generate_scenario(self, category: str, 
                         difficulty: str) -> Scenario:
        """Generate a new scenario dynamically"""
        
    def generate_hint(self, scenario: Scenario, 
                     container_state: Dict) -> str:
        """Generate contextual hint"""
        
    def validate_complex(self, scenario: Scenario, 
                        container: Container) -> ValidationResult:
        """Intelligent validation for complex tasks"""
```

## Data Models

### Configuration

```python
@dataclass
class Config:
    scenarios_path: str = "scenarios"
    database_path: str = "database/progress.db"
    logs_path: str = "logs"
    docker_config: DockerConfig = field(default_factory=DockerConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    ai_enabled: bool = False
    ai_config: Optional[AIConfig] = None
    
@dataclass
class DockerConfig:
    base_image_prefix: str = "lfcs-practice"
    default_distribution: str = "ubuntu"
    container_timeout: int = 3600  # 1 hour
    privileged: bool = True
    
@dataclass
class AIConfig:
    provider: str  # "openai", "anthropic", etc.
    api_key: str
    model: str
    temperature: float = 0.7
```

### Results

```python
@dataclass
class ValidationResult:
    passed: bool
    checks_passed: int
    checks_total: int
    check_results: List[CheckResult]
    feedback: str
    
@dataclass
class CheckResult:
    check_name: str
    passed: bool
    message: str
    expected: Optional[str]
    actual: Optional[str]
    
@dataclass
class SessionResult:
    scenario: Scenario
    validation_result: ValidationResult
    score: int
    duration: int
    passed: bool
    
@dataclass
class Statistics:
    total_attempts: int
    total_passed: int
    total_score: int
    average_score: float
    by_category: Dict[str, CategoryStats]
    current_streak: int
    best_streak: int
    achievements: List[Achievement]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Scenario loading completeness
*For any* valid YAML scenario file in the scenarios directory, when the system starts, the Scenario Loader should successfully load and parse that scenario without errors.
**Validates: Requirements 1.1, 1.5**

### Property 2: Category filtering correctness
*For any* category and difficulty combination, when a user requests a scenario with those filters, all returned scenarios should match the specified category and difficulty level.
**Validates: Requirements 1.2, 1.3**

### Property 3: Container isolation
*For any* practice session, when a container is created and destroyed, no artifacts from that session should persist on the host system or affect subsequent sessions.
**Validates: Requirements 2.1, 2.4**

### Property 4: Validation determinism
*For any* scenario and container state, running validation multiple times on the same unchanged state should produce identical results.
**Validates: Requirements 3.1, 3.5**

### Property 5: Validation feedback completeness
*For any* failed validation, the feedback should identify which specific checks failed and provide actionable information about what was expected versus what was found.
**Validates: Requirements 3.3, 3.4**

### Property 6: Score calculation consistency
*For any* validation result with the same number of passed checks and scenario difficulty, the calculated score should be identical across multiple calculations.
**Validates: Requirements 4.1**

### Property 7: Progress persistence
*For any* completed scenario, when the result is persisted to the database, querying the database immediately afterward should return that attempt with all correct details.
**Validates: Requirements 4.2, 4.4**

### Property 8: Statistics accuracy
*For any* set of recorded attempts, the calculated statistics (completion rate, average score, performance by category) should accurately reflect the sum and averages of those attempts.
**Validates: Requirements 4.3**

### Property 9: CLI command validation
*For any* invalid command or argument combination, the CLI should reject it with a clear error message and not proceed with execution.
**Validates: Requirements 5.5**

### Property 10: YAML validation strictness
*For any* YAML file with missing required fields or invalid structure, the Scenario Loader should reject it and report specific errors about what is missing or invalid.
**Validates: Requirements 6.1, 6.5**

### Property 11: Multi-distribution compatibility
*For any* scenario marked as distribution-agnostic (no specific distribution field), the scenario should execute successfully on Ubuntu, CentOS, and Rocky Linux containers.
**Validates: Requirements 8.1, 8.4**

### Property 12: Configuration override precedence
*For any* configuration setting, when both a config file value and an environment variable are present, the environment variable value should take precedence.
**Validates: Requirements 10.3**

### Property 13: Error recovery without data loss
*For any* error condition (container failure, validation error, database error), the system should handle it gracefully without losing previously recorded progress data.
**Validates: Requirements 11.3, 11.4**

### Property 14: Difficulty multiplier consistency
*For any* two scenarios with different difficulty levels but identical validation results, the harder scenario should always award more points than the easier one.
**Validates: Requirements 12.3**

## Error Handling

### Error Categories

1. **Docker Errors**
   - Docker daemon not running → Detect and provide installation/startup instructions
   - Image not found → Attempt to build, fallback to pull, provide manual instructions
   - Container creation failure → Log details, suggest resource checks, cleanup partial state
   - Container execution timeout → Warn user, offer to extend time or terminate

2. **Scenario Errors**
   - YAML parsing error → Report line number and specific syntax issue
   - Missing required fields → List all missing fields
   - Invalid validation rules → Explain which rule is invalid and why
   - Scenario not found → Suggest similar scenarios, offer to list available ones

3. **Validation Errors**
   - Command execution failure → Capture stderr, provide to user
   - Validation script not found → Check paths, suggest script installation
   - Timeout during validation → Report which check timed out
   - Unexpected validation result → Log full context for debugging

4. **Database Errors**
   - Database locked → Retry with exponential backoff
   - Corruption detected → Attempt recovery, offer to reinitialize
   - Schema mismatch → Run migrations automatically
   - Disk full → Report space issue, suggest cleanup

5. **AI Errors** (when enabled)
   - API key invalid → Provide configuration instructions
   - Rate limit exceeded → Fallback to static scenarios
   - Network timeout → Retry with backoff, fallback to static
   - Invalid response → Log for debugging, fallback to static

### Error Handling Strategy

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: Dict) -> ErrorResponse:
        """Central error handling with context"""
        
    def log_error(self, error: Exception, context: Dict) -> None:
        """Log error with full context"""
        
    def suggest_recovery(self, error: Exception) -> List[str]:
        """Provide recovery suggestions"""
```

All errors are logged to `logs/lfcs-practice-{date}.log` with:
- Timestamp
- Error type and message
- Full stack trace
- Context (scenario ID, container ID, user action)
- System state (Docker status, disk space, etc.)

## Testing Strategy

### Unit Testing

The system will use **pytest** as the testing framework for Python. Unit tests will verify individual components in isolation:

**Core Components:**
- `test_scenario_loader.py`: Test YAML parsing, filtering, validation
- `test_docker_manager.py`: Test container lifecycle (using Docker test containers)
- `test_validator.py`: Test validation logic with mock containers
- `test_scorer.py`: Test score calculation and database operations
- `test_cli.py`: Test command parsing and routing

**Test Organization:**
```
tests/
├── unit/
│   ├── test_scenario_loader.py
│   ├── test_docker_manager.py
│   ├── test_validator.py
│   ├── test_scorer.py
│   └── test_cli.py
├── integration/
│   ├── test_full_session.py
│   ├── test_docker_validation.py
│   └── test_database_persistence.py
└── fixtures/
    ├── sample_scenarios.yaml
    └── test_config.yaml
```

### Property-Based Testing

The system will use **Hypothesis** for property-based testing in Python. Each correctness property from the design will be implemented as a property-based test:

**Configuration:**
- Minimum 100 iterations per property test
- Custom generators for scenarios, validation rules, and container states
- Shrinking enabled to find minimal failing examples

**Property Test Requirements:**
- Each test must include a comment with the format: `# Feature: lfcs-practice-environment, Property X: <property description>`
- Each test must reference the requirements it validates
- Tests should use realistic data generators that respect domain constraints

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st

# Feature: lfcs-practice-environment, Property 2: Category filtering correctness
@given(
    category=st.sampled_from(['networking', 'storage', 'users_groups']),
    difficulty=st.sampled_from(['easy', 'medium', 'hard'])
)
def test_category_filtering_correctness(category, difficulty):
    """For any category and difficulty, returned scenarios should match filters"""
    # Test implementation
```

### Integration Testing

Integration tests verify end-to-end workflows:
- Complete practice session from start to finish
- Docker container creation, task execution, validation, cleanup
- Database persistence across multiple sessions
- Error recovery scenarios

### Test Data

**Fixtures:**
- Sample YAML scenarios covering all categories and difficulties
- Mock Docker containers for testing without actual Docker
- Pre-populated test databases with known data
- Configuration files for different test scenarios

**Generators for Property Tests:**
- Scenario generator: Creates valid Scenario objects with random but realistic data
- Validation rules generator: Creates various combinations of checks
- Container state generator: Simulates different container states for validation testing

## Implementation Notes

### Technology Stack

- **Language:** Python 3.9+
- **CLI Framework:** argparse (standard library)
- **Docker SDK:** docker-py
- **Database:** SQLite3 (standard library)
- **YAML Parser:** PyYAML
- **Testing:** pytest, Hypothesis
- **AI Integration:** OpenAI SDK, Anthropic SDK (optional)
- **Logging:** Python logging module

### Dependencies

```
# requirements.txt
docker>=6.0.0
PyYAML>=6.0
pytest>=7.0.0
hypothesis>=6.0.0
openai>=1.0.0  # optional
anthropic>=0.3.0  # optional
```

### Directory Structure

```
lfcs-practice-tool/
├── src/
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main_cli.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── scenario_loader.py
│   ├── docker_manager/
│   │   ├── __init__.py
│   │   └── container.py
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── db_manager.py
│   ├── ai/  # optional
│   │   ├── __init__.py
│   │   ├── scenario_generator.py
│   │   └── validator.py
│   └── main.py
├── scenarios/
│   ├── networking/
│   ├── storage/
│   ├── users_groups/
│   ├── operations_deployment/
│   └── essential_commands/
├── docker/
│   ├── base_images/
│   │   ├── ubuntu/Dockerfile
│   │   ├── centos/Dockerfile
│   │   └── rocky/Dockerfile
│   └── validation_scripts/
├── database/
│   └── schema.sql
├── config/
│   ├── config.yaml
│   └── ai_config.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── logs/
├── requirements.txt
├── setup.py
└── README.md
```

### Performance Considerations

- **Container Caching:** Reuse base images, don't rebuild unnecessarily
- **Database Indexing:** Index on category, timestamp for fast queries
- **Lazy Loading:** Load scenarios on-demand rather than all at once
- **Connection Pooling:** Reuse Docker client connections
- **Async Operations:** Consider async for AI calls to avoid blocking

### Security Considerations

- **Container Isolation:** Use Docker security features (AppArmor, seccomp)
- **Resource Limits:** Set CPU and memory limits on containers
- **API Key Storage:** Never commit API keys, use environment variables
- **Input Validation:** Sanitize all user inputs before passing to Docker
- **Privilege Management:** Run containers with minimum required privileges

### Extensibility

The design supports future extensions:
- **New Categories:** Add YAML files to scenarios directory
- **New Distributions:** Add Dockerfile to docker/base_images
- **Custom Validators:** Add scripts to docker/validation_scripts
- **New AI Providers:** Implement AIModule interface for different providers
- **Web Interface:** Core engine can be wrapped with Flask/FastAPI
- **Multi-user Support:** Extend database schema with user tables
