# Validation Scripts

This directory contains custom validation scripts for complex LFCS practice scenarios. Validation scripts provide flexible, programmable validation logic that goes beyond simple command checks.

## Table of Contents

- [Overview](#overview)
- [Script Interface](#script-interface)
- [Using Validation Scripts](#using-validation-scripts)
- [Templates](#templates)
- [Example Scripts](#example-scripts)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Validation scripts are executed inside Docker containers to verify that users have correctly completed practice tasks. They provide a way to implement complex validation logic that cannot be expressed through simple command, file, or service checks.

### When to Use Custom Scripts

Use custom validation scripts when you need to:

- Validate complex multi-step configurations
- Perform calculations or comparisons
- Check relationships between multiple system components
- Implement custom logic that doesn't fit standard check types
- Validate state across multiple files or services

### Supported Languages

- **Bash** (`.sh` files) - Best for system commands and simple checks
- **Python** (`.py` files) - Best for complex logic and data processing

## Script Interface

### Exit Codes

Validation scripts communicate results through exit codes:

- **Exit code 0**: Validation passed ✓
- **Exit code non-zero**: Validation failed ✗

### Standard Output

- All output to `stdout` is captured and displayed to the user
- Use clear, descriptive messages to explain what was checked
- Include both success and failure messages
- Format output for readability (use symbols like ✓ and ✗)

### Standard Error

- Output to `stderr` is captured but typically indicates script errors
- Use `stderr` for debugging information, not validation feedback

### Arguments

Scripts receive arguments from the scenario YAML file:

```yaml
validation:
  checks:
    - type: custom
      script_path: /validation/my_script.sh
      args: ["arg1", "arg2", "arg3"]
      expected_exit_code: 0
      description: "Custom validation description"
```

Arguments are passed as command-line parameters:
- Bash: `$1`, `$2`, `$3`, etc.
- Python: `sys.argv[1]`, `sys.argv[2]`, `sys.argv[3]`, etc.

### Script Location

Scripts must be placed in the `docker/validation_scripts/` directory. They are mounted into containers at `/validation/` during execution.

## Using Validation Scripts

### 1. Create Your Script

Create a new script in `docker/validation_scripts/`:

```bash
# Bash script
touch docker/validation_scripts/my_validation.sh
chmod +x docker/validation_scripts/my_validation.sh
```

```python
# Python script
touch docker/validation_scripts/my_validation.py
chmod +x docker/validation_scripts/my_validation.py
```

### 2. Implement Validation Logic

Use the templates as a starting point:
- `template.sh` for Bash scripts
- `template.py` for Python scripts

### 3. Add to Scenario YAML

Reference your script in the scenario's validation section:

```yaml
id: my_scenario_01
category: networking
difficulty: medium
task: "Configure network interface with static IP"
validation:
  checks:
    - type: custom
      script_path: /validation/my_validation.sh
      args: ["eth0", "192.168.1.100"]
      expected_exit_code: 0
      description: "Validate network configuration"
points: 50
```

### 4. Test Your Script

Test scripts locally before deploying:

```bash
# Test bash script
bash docker/validation_scripts/my_validation.sh arg1 arg2

# Test python script
python3 docker/validation_scripts/my_validation.py arg1 arg2
```

## Templates

### Bash Template (`template.sh`)

A complete Bash script template with:
- Argument parsing
- Helper functions (`pass()`, `fail()`)
- Common validation patterns
- Error handling with `set -e` and `set -u`

**Usage:**
```bash
cp docker/validation_scripts/template.sh docker/validation_scripts/my_script.sh
# Edit my_script.sh with your validation logic
```

### Python Template (`template.py`)

A complete Python script template with:
- Argument parsing
- Helper functions (`validate_pass()`, `validate_fail()`, `run_command()`)
- File and command utilities
- Type hints and documentation

**Usage:**
```bash
cp docker/validation_scripts/template.py docker/validation_scripts/my_script.py
# Edit my_script.py with your validation logic
```

## Example Scripts

### `validate_network_config.sh`

Validates complex network configurations including:
- Interface existence and state
- IP address assignment
- Default gateway configuration
- DNS resolver configuration

**Usage in YAML:**
```yaml
- type: custom
  script_path: /validation/validate_network_config.sh
  args: ["eth0", "192.168.1.100", "192.168.1.1"]
  description: "Validate network configuration"
```

**Arguments:**
1. Interface name (e.g., `eth0`)
2. Expected IP address (e.g., `192.168.1.100`)
3. Expected gateway (optional, e.g., `192.168.1.1`)

### `validate_user_setup.py`

Validates user and group configurations including:
- User existence and properties (UID, shell, home directory)
- Group membership
- Home directory permissions
- Sudo access

**Usage in YAML:**
```yaml
- type: custom
  script_path: /validation/validate_user_setup.py
  args: ["alice", "2000", "developers,sudo"]
  description: "Validate user configuration"
```

**Arguments:**
1. Username (required)
2. Expected UID (optional)
3. Comma-separated list of expected groups (optional)

### `validate_systemd_service.sh`

Validates systemd service configuration and state including:
- Service file existence
- Service active/inactive state
- Service enabled state
- Recent error logs

**Usage in YAML:**
```yaml
- type: custom
  script_path: /validation/validate_systemd_service.sh
  args: ["nginx", "active", "yes"]
  description: "Validate nginx service"
```

**Arguments:**
1. Service name (required, e.g., `nginx`)
2. Expected state (optional, default: `active`)
3. Check enabled (optional, default: `yes`)

### `validate_storage_config.py`

Validates storage and filesystem configurations including:
- Mount point existence and state
- Filesystem type and device
- LVM volume detection
- Filesystem usage and permissions
- Write access verification

**Usage in YAML:**
```yaml
- type: custom
  script_path: /validation/validate_storage_config.py
  args: ["/mnt/data", "ext4", "/dev/sdb1"]
  description: "Validate storage mount"
```

**Arguments:**
1. Mount point (required, e.g., `/mnt/data`)
2. Expected filesystem type (optional, e.g., `ext4`)
3. Expected device (optional, e.g., `/dev/sdb1`)

## Best Practices

### Script Design

1. **Single Responsibility**: Each script should validate one logical aspect
2. **Clear Output**: Provide descriptive messages for both success and failure
3. **Fail Fast**: Exit immediately when a critical check fails
4. **Informative Failures**: Explain what was expected vs. what was found
5. **Defensive Programming**: Handle missing files, commands, and edge cases

### Error Handling

```bash
# Bash: Use set -e to exit on errors
set -e
set -u

# Check command availability
if ! command -v some_command &> /dev/null; then
    fail "Required command not found"
fi
```

```python
# Python: Use try-except for error handling
try:
    result = subprocess.run(...)
except subprocess.TimeoutExpired:
    validate_fail("Command timed out")
except Exception as e:
    validate_fail(f"Unexpected error: {e}")
```

### Performance

- Keep scripts fast (< 5 seconds execution time)
- Avoid unnecessary operations
- Use timeouts for external commands
- Cache results when checking multiple related items

### Security

- Validate and sanitize all input arguments
- Avoid shell injection vulnerabilities
- Use absolute paths for commands
- Don't trust user-provided data

### Maintainability

- Add comments explaining complex logic
- Use meaningful variable names
- Follow language conventions (shellcheck for Bash, PEP 8 for Python)
- Include usage documentation in script headers

## Troubleshooting

### Script Not Found

**Problem**: `Custom script validation failed: script not found`

**Solution**: 
- Ensure script is in `docker/validation_scripts/`
- Check script path in YAML uses `/validation/` prefix
- Verify script has execute permissions (`chmod +x`)

### Permission Denied

**Problem**: `Permission denied` when executing script

**Solution**:
```bash
chmod +x docker/validation_scripts/your_script.sh
```

### Script Fails Unexpectedly

**Problem**: Script exits with non-zero code but should pass

**Solution**:
- Test script locally with same arguments
- Check for missing dependencies in container
- Review script output for error messages
- Add debug output to identify failure point

### Timeout Issues

**Problem**: Script takes too long to execute

**Solution**:
- Optimize script logic
- Remove unnecessary operations
- Add timeouts to external commands
- Consider breaking into multiple checks

### Argument Parsing Errors

**Problem**: Script receives wrong number or type of arguments

**Solution**:
- Verify YAML `args` array matches script expectations
- Add argument validation at script start
- Provide default values for optional arguments
- Document required arguments in script header

## Advanced Topics

### Combining Multiple Checks

You can use multiple custom scripts in a single scenario:

```yaml
validation:
  checks:
    - type: custom
      script_path: /validation/check_network.sh
      args: ["eth0"]
      description: "Validate network interface"
    
    - type: custom
      script_path: /validation/check_firewall.sh
      args: ["80", "443"]
      description: "Validate firewall rules"
    
    - type: command
      command: "ping -c 1 8.8.8.8"
      description: "Verify internet connectivity"
```

### Sharing Code Between Scripts

For common functionality, create library scripts:

```bash
# docker/validation_scripts/lib/common.sh
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Script must run as root"
        return 1
    fi
}

# Source in your scripts
source /validation/lib/common.sh
check_root || fail "Root access required"
```

### Dynamic Validation

Scripts can adapt validation based on system state:

```python
# Detect distribution and adjust checks
def get_distribution():
    if os.path.exists('/etc/redhat-release'):
        return 'rhel'
    elif os.path.exists('/etc/debian_version'):
        return 'debian'
    return 'unknown'

distro = get_distribution()
if distro == 'rhel':
    # RHEL-specific validation
    pass
elif distro == 'debian':
    # Debian-specific validation
    pass
```

## Contributing

When adding new validation scripts:

1. Use templates as starting points
2. Follow naming convention: `validate_<purpose>.{sh|py}`
3. Document arguments and usage in script header
4. Add example usage to this README
5. Test thoroughly in all supported distributions
6. Consider edge cases and error conditions

## Support

For issues or questions about validation scripts:

1. Check this README for common solutions
2. Review example scripts for patterns
3. Test scripts locally before deploying
4. Check container logs for detailed error messages
