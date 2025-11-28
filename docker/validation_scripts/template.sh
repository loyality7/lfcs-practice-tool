#!/bin/bash
#
# Bash Validation Script Template
#
# This template provides a standard structure for custom validation scripts.
# Validation scripts are executed inside Docker containers to verify task completion.
#
# INTERFACE:
# - Exit code 0 indicates validation passed
# - Exit code non-zero indicates validation failed
# - Output to stdout is captured and displayed to the user
# - Arguments can be passed from the scenario YAML file
#
# USAGE:
# The script receives arguments from the CustomCheck in the scenario:
#   args:
#     - arg1
#     - arg2
#
# EXAMPLE SCENARIO YAML:
#   validation:
#     checks:
#       - type: custom
#         script_path: /validation/my_script.sh
#         args: ["expected_value", "threshold"]
#         expected_exit_code: 0
#         description: "Custom validation for complex scenario"

set -e  # Exit on error
set -u  # Exit on undefined variable

# Parse arguments
# ARG1="${1:-default_value}"
# ARG2="${2:-default_value}"

# Validation logic goes here
# Example: Check if a specific condition is met

# Function to print success message and exit
pass() {
    echo "✓ Validation passed: $1"
    exit 0
}

# Function to print failure message and exit
fail() {
    echo "✗ Validation failed: $1"
    exit 1
}

# Example validation checks:

# Check if a file exists
# if [ ! -f "/path/to/file" ]; then
#     fail "Required file not found"
# fi

# Check if a command succeeds
# if ! command -v some_command &> /dev/null; then
#     fail "Required command not found"
# fi

# Check if a value matches expected
# ACTUAL=$(some_command)
# if [ "$ACTUAL" != "$EXPECTED" ]; then
#     fail "Expected $EXPECTED but got $ACTUAL"
# fi

# If all checks pass
pass "All validation checks completed successfully"
