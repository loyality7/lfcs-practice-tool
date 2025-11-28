# Contributing to LFCS Practice Tool

Thank you for your interest in contributing to the LFCS Practice Tool! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/loyality7/lfcs-practice-tool/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Docker version)
   - Relevant logs or error messages

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach
   - Any relevant examples or mockups

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write or update tests**
5. **Run tests and ensure they pass**
   ```bash
   pytest
   ```
6. **Format your code**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   ```
7. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
8. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
9. **Create a Pull Request**

## 📝 Adding New Scenarios

Scenarios are the heart of the practice tool. Here's how to add new ones:

### 1. Choose a Category

Place your scenario in the appropriate directory:
- `scenarios/essential_commands/`
- `scenarios/networking/`
- `scenarios/storage/`
- `scenarios/users_groups/`
- `scenarios/operations_deployment/`

### 2. Choose a Difficulty

Create your scenario in the appropriate subdirectory:
- `easy/` - Basic, single-step tasks
- `medium/` - Multi-step tasks requiring understanding
- `hard/` - Complex scenarios, troubleshooting, advanced configs

### 3. Create the YAML File

Use this template:

```yaml
id: category_difficulty_description_01
category: networking  # or storage, users_groups, etc.
difficulty: medium    # easy, medium, or hard
distribution: null    # null (all), ubuntu, centos, or rocky
task: |
  Clear, concise task description.
  
  Provide context and requirements.
  Be specific about what needs to be accomplished.
  
  Example: Configure the network interface eth0 with:
  - IP address: 192.168.1.100
  - Netmask: 255.255.255.0
  - Gateway: 192.168.1.1

setup_commands:
  - "command to prepare the environment"
  - "another setup command if needed"

validation:
  checks:
    - type: command
      command: "command to verify task completion"
      expected_exit_code: 0
      expected_output: "expected output (optional)"
      regex_match: "regex pattern (optional)"
      description: "What this check verifies"
    
    - type: file
      path: "/path/to/file"
      should_exist: true
      permissions: "0644"
      owner: "root"
      group: "root"
      content_contains: "expected content"
      description: "File check description"
    
    - type: service
      service_name: "service-name"
      should_be_running: true
      should_be_enabled: true
      description: "Service check description"

points: 100  # Base points (will be multiplied by difficulty)
hints:
  - "Helpful hint without giving away the answer"
  - "Another hint if needed"
  - "Progressive hints from general to specific"
time_limit: 600  # seconds (optional)
```

### 4. Test Your Scenario

```bash
# Test the scenario
lfcs-practice start --category your_category --difficulty your_difficulty

# Verify validation works correctly
# Try both correct and incorrect solutions
```

### 5. Naming Conventions

- **File name**: `descriptive_name_01.yaml`
- **Scenario ID**: `category_difficulty_description_01`
- Use lowercase with underscores
- Number scenarios sequentially (01, 02, 03...)

### 6. Best Practices

**Task Description:**
- Be clear and specific
- Include all requirements
- Provide context when needed
- Use proper formatting

**Validation:**
- Test multiple aspects of the solution
- Include both positive and negative checks
- Provide descriptive check names
- Test edge cases

**Hints:**
- Start general, get more specific
- Don't give away the complete solution
- Guide thinking, not just commands
- 2-4 hints is usually sufficient

**Points:**
- Easy: 50-100 points
- Medium: 100-150 points
- Hard: 150-200 points

## 🧪 Testing Guidelines

### Unit Tests

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Follow existing test patterns

```python
def test_feature_does_something():
    """Test that feature behaves correctly"""
    # Arrange
    setup_test_data()
    
    # Act
    result = feature_function()
    
    # Assert
    assert result == expected_value
```

### Property-Based Tests

For universal properties, use Hypothesis:

```python
from hypothesis import given, strategies as st

@given(st.text(), st.integers())
def test_property_holds_for_all_inputs(text, number):
    """Test that property holds for any valid input"""
    result = function_under_test(text, number)
    assert property_holds(result)
```

### Integration Tests

Test complete workflows:
- Full practice session
- Docker container lifecycle
- Database persistence
- Error recovery

## 📋 Code Style

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints where appropriate
- Write docstrings for all public functions

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### Commit Messages

Use conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat(scenarios): add advanced networking scenarios

fix(docker): handle container cleanup errors gracefully

docs(readme): update installation instructions

test(validator): add property-based tests for validation
```

## 🔍 Code Review Process

All contributions go through code review:

1. **Automated Checks**: Tests, linting, coverage
2. **Manual Review**: Code quality, design, documentation
3. **Feedback**: Reviewers may request changes
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge to main branch

## 📚 Documentation

Update documentation when:
- Adding new features
- Changing existing behavior
- Adding new configuration options
- Creating new scenarios

Documentation locations:
- `README.md` - Main documentation
- `docs/` - Detailed documentation
- Code docstrings - API documentation
- Scenario YAML - Inline documentation

## 🎯 Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/loyality7/lfcs-practice-tool.git
cd lfcs-practice-tool
pip install -e ".[dev]"
```

### 2. Build Docker Images

```bash
cd docker/base_images
./build_all.sh
```

### 3. Run Tests

```bash
pytest
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## 🐛 Debugging

### Enable Debug Logging

```bash
export LFCS_LOG_LEVEL=DEBUG
lfcs-practice start
```

### Check Logs

```bash
tail -f logs/lfcs-practice-$(date +%Y%m%d).log
```

### Docker Debugging

```bash
# List containers
docker ps -a

# Check container logs
docker logs <container-id>

# Access container
docker exec -it <container-id> /bin/bash
```

## 📞 Getting Help

- 💬 [Discussions](https://github.com/loyality7/lfcs-practice-tool/discussions)
- 🐛 [Issues](https://github.com/loyality7/lfcs-practice-tool/issues)
- 📧 Email: your-email@example.com

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!
