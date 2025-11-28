#!/bin/bash
#
# Network Configuration Validation Script
#
# Validates complex network configurations including:
# - IP address assignment
# - Routing table entries
# - DNS configuration
# - Network interface state
#
# Arguments:
#   $1 - Interface name (e.g., eth0)
#   $2 - Expected IP address (e.g., 192.168.1.100)
#   $3 - Expected gateway (optional)

set -e
set -u

INTERFACE="${1:-eth0}"
EXPECTED_IP="${2:-}"
EXPECTED_GATEWAY="${3:-}"

fail() {
    echo "✗ Network validation failed: $1"
    exit 1
}

pass() {
    echo "✓ Network validation passed: $1"
    exit 0
}

# Check if interface exists
if ! ip link show "$INTERFACE" &> /dev/null; then
    fail "Interface $INTERFACE does not exist"
fi

# Check if interface is up
if ! ip link show "$INTERFACE" | grep -q "state UP"; then
    fail "Interface $INTERFACE is not up"
fi

# Check IP address if specified
if [ -n "$EXPECTED_IP" ]; then
    ACTUAL_IP=$(ip addr show "$INTERFACE" | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    
    if [ -z "$ACTUAL_IP" ]; then
        fail "No IP address assigned to $INTERFACE"
    fi
    
    if [ "$ACTUAL_IP" != "$EXPECTED_IP" ]; then
        fail "Expected IP $EXPECTED_IP on $INTERFACE but found $ACTUAL_IP"
    fi
    
    echo "✓ IP address $ACTUAL_IP correctly configured on $INTERFACE"
fi

# Check default gateway if specified
if [ -n "$EXPECTED_GATEWAY" ]; then
    if ! ip route | grep -q "default via $EXPECTED_GATEWAY"; then
        ACTUAL_GATEWAY=$(ip route | grep "^default" | awk '{print $3}')
        fail "Expected gateway $EXPECTED_GATEWAY but found $ACTUAL_GATEWAY"
    fi
    
    echo "✓ Default gateway $EXPECTED_GATEWAY correctly configured"
fi

# Check DNS configuration
if [ -f /etc/resolv.conf ]; then
    if ! grep -q "nameserver" /etc/resolv.conf; then
        fail "No nameservers configured in /etc/resolv.conf"
    fi
    echo "✓ DNS nameservers configured"
fi

pass "All network configuration checks passed"
