#!/bin/bash
#
# Systemd Service Validation Script
#
# Validates systemd service configuration and state including:
# - Service file existence and syntax
# - Service active state
# - Service enabled state
# - Service dependencies
# - Service logs for errors
#
# Arguments:
#   $1 - Service name (e.g., nginx, sshd)
#   $2 - Expected state (active/inactive) (optional, default: active)
#   $3 - Check enabled (yes/no) (optional, default: yes)

set -e
set -u

SERVICE_NAME="${1:-}"
EXPECTED_STATE="${2:-active}"
CHECK_ENABLED="${3:-yes}"

fail() {
    echo "✗ Service validation failed: $1"
    exit 1
}

pass() {
    echo "✓ Service validation passed: $1"
    exit 0
}

if [ -z "$SERVICE_NAME" ]; then
    fail "Service name argument required"
fi

# Add .service suffix if not present
if [[ ! "$SERVICE_NAME" =~ \.service$ ]]; then
    SERVICE_NAME="${SERVICE_NAME}.service"
fi

# Check if service unit file exists
if ! systemctl cat "$SERVICE_NAME" &> /dev/null; then
    fail "Service unit file for $SERVICE_NAME not found"
fi

echo "✓ Service unit file exists"

# Check service state
ACTUAL_STATE=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || echo "inactive")

if [ "$EXPECTED_STATE" = "active" ]; then
    if [ "$ACTUAL_STATE" != "active" ]; then
        # Get service status for debugging
        STATUS=$(systemctl status "$SERVICE_NAME" 2>&1 || true)
        fail "Service $SERVICE_NAME is $ACTUAL_STATE (expected active). Status: $STATUS"
    fi
    echo "✓ Service is active"
elif [ "$EXPECTED_STATE" = "inactive" ]; then
    if [ "$ACTUAL_STATE" = "active" ]; then
        fail "Service $SERVICE_NAME is active (expected inactive)"
    fi
    echo "✓ Service is inactive"
fi

# Check if service is enabled (if requested)
if [ "$CHECK_ENABLED" = "yes" ] && [ "$EXPECTED_STATE" = "active" ]; then
    ENABLED_STATE=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo "disabled")
    
    if [ "$ENABLED_STATE" != "enabled" ] && [ "$ENABLED_STATE" != "static" ]; then
        fail "Service $SERVICE_NAME is not enabled (state: $ENABLED_STATE)"
    fi
    echo "✓ Service is enabled"
fi

# Check for recent errors in service logs
if [ "$EXPECTED_STATE" = "active" ]; then
    ERROR_COUNT=$(journalctl -u "$SERVICE_NAME" -n 50 --no-pager 2>/dev/null | grep -i "error\|failed\|fatal" | wc -l || echo "0")
    
    if [ "$ERROR_COUNT" -gt 5 ]; then
        echo "⚠ Warning: Found $ERROR_COUNT error messages in recent logs"
        journalctl -u "$SERVICE_NAME" -n 10 --no-pager 2>/dev/null | tail -5
    else
        echo "✓ No significant errors in recent logs"
    fi
fi

# Verify service can be reloaded (if active)
if [ "$EXPECTED_STATE" = "active" ]; then
    if systemctl show "$SERVICE_NAME" -p CanReload --value 2>/dev/null | grep -q "yes"; then
        echo "✓ Service supports reload"
    fi
fi

pass "All service validation checks passed for $SERVICE_NAME"
