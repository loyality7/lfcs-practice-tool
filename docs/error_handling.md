# Error Handling System

## Overview

The LFCS Practice Tool includes a comprehensive error handling system that provides:
- Centralized error categorization and handling
- User-friendly error messages
- Actionable recovery suggestions
- Detailed logging with context
- Automatic retry logic for transient errors
- Graceful degradation for non-critical errors

## Architecture

### Error Handler (`src/utils/error_handler.py`)

The `ErrorHandler` class is the central component that:
1. Categorizes errors into specific types (Docker, Database, Validation, etc.)
2. Determines error severity (Critical, Error, Warning, Info)
3. Generates user-friendly error messages
4. Provides recovery suggestions
5. Logs errors with full context
6. Determines retry and exit behavior

### Error Categories

- **DOCKER**: Docker daemon, container, and image errors
- **SCENARIO**: YAML parsing and scenario loading errors
- **VALIDATION**: Task validation and check execution errors
- **DATABASE**: SQLite database errors
- **AI**: AI service errors (when enabled)
- **CONFIGURATION**: Configuration file and settings errors
- **SYSTEM**: File system and permission errors
- **UNKNOWN**: Uncategorized errors

### Error Severity Levels

- **CRITICAL**: System cannot continue, must exit
- **ERROR**: Operation failed but system can continue
- **WARNING**: Potential issue but operation succeeded
- **INFO**: Informational message

## Usage

### Basic Error Handling

```python
from src.utils.error_handler import ErrorHandler, ErrorContext

handler = ErrorHandler()

try:
    # Your code here
    pass
except Exception as e:
    context = ErrorContext(
        scenario_id="test_scenario_01",
        user_action="create_container"
    )
    response = handler.handle_error(e, context)
    
    # Display error to user
    print(handler.format_error_for_user(response))
    
    # Check if should exit
    if response.should_exit:
        sys.exit(1)
```

### Convenience Functions

For common error types, use convenience functions:

```python
from src.utils.error_handler import (
    handle_docker_error,
    handle_database_error,
    handle_validation_error
)

# Docker errors
try:
    container = docker_manager.create_container(...)
except DockerException as e:
    context = ErrorContext(user_action="create_container")
    response = handle_docker_error(e, context)
    print(handler.format_error_for_user(response))

# Database errors with retry logic
try:
    scorer.record_attempt(...)
except sqlite3.OperationalError as e:
    context = ErrorContext(scenario_id="test_01")
    should_retry, response = handle_database_error(e, context)
    if should_retry:
        # Implement retry logic
        pass
```

### Error Context

Provide context to help with debugging and user guidance:

```python
context = ErrorContext(
    scenario_id="networking_easy_01",
    container_id="abc123",
    user_action="validate_scenario",
    category="networking",
    difficulty="easy",
    additional_info={
        'check_name': 'verify_interface',
        'check_index': 2
    }
)
```

## Integration

### Docker Manager

The Docker Manager integrates error handling for:
- Docker daemon not available
- Image not found
- Container creation failures
- Command execution errors
- Container cleanup errors

### Database Manager

The Database Manager integrates error handling for:
- Database locked (with automatic retry)
- Database corruption
- Disk space issues
- Permission errors

### Validation System

The Validator integrates error handling for:
- Command execution failures
- Validation script errors
- Timeout errors
- Unexpected validation results

### Core Engine

The Engine integrates error handling for:
- Session initialization errors
- Component initialization failures
- Session execution errors
- Cleanup errors

## Error Recovery

### Automatic Retry

The system automatically retries transient errors:
- Database locked: 3 retries with exponential backoff
- Docker timeout: Retry once

### Recovery Suggestions

Each error type provides specific recovery suggestions:

**Docker Errors:**
- Install Docker
- Start Docker daemon
- Build base images
- Check permissions
- Free disk space

**Database Errors:**
- Wait and retry
- Close other instances
- Reset database
- Free disk space
- Check permissions

**Scenario Errors:**
- Check YAML syntax
- Validate scenario structure
- Try different filters
- Check file paths

**Validation Errors:**
- Check container status
- Verify validation scripts
- Increase timeout
- Check container logs

## Logging

All errors are logged to `logs/lfcs-practice-{date}.log` with:
- Timestamp
- Error category and severity
- Error type and message
- Full stack trace (for errors and critical issues)
- Context information (scenario ID, container ID, user action)
- System state (for critical errors)

### Log Levels

- CRITICAL: Critical errors that require exit
- ERROR: Operation failures
- WARNING: Potential issues
- INFO: Informational messages
- DEBUG: Detailed debugging information

## Best Practices

1. **Always provide context**: Include scenario ID, container ID, and user action
2. **Use convenience functions**: For common error types (Docker, Database, Validation)
3. **Check should_exit**: Exit gracefully for critical errors
4. **Implement retry logic**: For transient errors (database locked, timeouts)
5. **Display user-friendly messages**: Use `format_error_for_user()` for output
6. **Log all errors**: Even if handled gracefully
7. **Preserve error chains**: Use `raise ... from e` to maintain error context

## Testing

The error handling system includes comprehensive unit tests:
- Error categorization
- Severity determination
- User message generation
- Recovery suggestions
- Retry logic
- Context handling
- Error formatting

Run tests:
```bash
pytest tests/unit/test_error_handler.py -v
```

## Examples

### Example 1: Docker Daemon Not Running

```
======================================================================
ERROR: DOCKER
======================================================================

Docker daemon is not running or not accessible.
The LFCS Practice Tool requires Docker to create isolated practice environments.

RECOVERY SUGGESTIONS:
  1. Install Docker: https://docs.docker.com/get-docker/
  2. Start Docker daemon: sudo systemctl start docker (Linux) or start Docker Desktop (Mac/Windows)
  3. Check Docker status: docker ps
  4. Verify Docker installation: docker --version

======================================================================
This is a critical error. The program will exit.
======================================================================
```

### Example 2: Database Locked

```
======================================================================
ERROR: DATABASE
======================================================================

Database is locked by another process.
Another instance of the tool may be running, or the database is being accessed.

RECOVERY SUGGESTIONS:
  1. Wait a moment and try again
  2. Close other instances of the tool
  3. Check for processes using the database: lsof database/progress.db
  4. If persistent, restart your system

======================================================================
```

### Example 3: Image Not Found

```
======================================================================
ERROR: DOCKER
======================================================================

Docker image not found.
The required base image for this scenario is not available on your system.

RECOVERY SUGGESTIONS:
  1. Build base images: cd docker/base_images && ./build_all.sh
  2. Pull image manually: docker pull <image-name>
  3. Check available images: docker images

======================================================================
```

## Future Enhancements

Potential improvements to the error handling system:
- Error metrics and analytics
- Error notification system
- Automated error reporting
- Error recovery automation
- Custom error handlers per component
- Error rate limiting
- Error aggregation and deduplication
