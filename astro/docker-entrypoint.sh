#!/bin/sh
set -e

# Set default values
PORT=${PORT:-8080}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

# Export variables for envsubst
export PORT
export BACKEND_URL

# Extract DNS resolver from /etc/resolv.conf (Railway configures this)
# Use the first nameserver found, or fallback to 8.8.8.8
RAW_RESOLVER=$(grep -E '^nameserver' /etc/resolv.conf | head -1 | awk '{print $2}' || echo "8.8.8.8")

# Format IPv6 addresses with square brackets for nginx (e.g., fd12::10 -> [fd12::10])
# Check if it's an IPv6 address (contains colons but no dots)
if echo "${RAW_RESOLVER}" | grep -qE '^[0-9a-fA-F:]+$' && ! echo "${RAW_RESOLVER}" | grep -qE '\.'; then
    # IPv6 address - wrap in square brackets
    RESOLVER="[${RAW_RESOLVER}]"
else
    # IPv4 address - use as is
    RESOLVER="${RAW_RESOLVER}"
fi

# Extract hostname from BACKEND_URL for DNS resolution check
BACKEND_HOST=$(echo "${BACKEND_URL}" | sed -E 's|^https?://||' | sed -E 's|:.*$||')

# For local testing: If BACKEND_URL uses host.docker.internal, try to resolve it to IP
# This helps when nginx resolver doesn't work with host.docker.internal
if [ "${BACKEND_HOST}" = "host.docker.internal" ]; then
    # Try to get IP for host.docker.internal
    HOST_IP=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}' | head -1)
    if [ -n "${HOST_IP}" ]; then
        echo "Resolved host.docker.internal to IP: ${HOST_IP}"
        # Replace host.docker.internal with IP in BACKEND_URL for nginx config
        BACKEND_URL=$(echo "${BACKEND_URL}" | sed "s|host.docker.internal|${HOST_IP}|g")
        export BACKEND_URL
        echo "Updated BACKEND_URL to use IP: ${BACKEND_URL}"
    else
        echo "WARNING: Could not resolve host.docker.internal to IP"
        echo "For local testing, consider using IP directly in BACKEND_URL"
    fi
fi

# Log configuration for debugging
echo "=== Nginx Configuration ==="
echo "PORT: ${PORT}"
echo "BACKEND_URL: ${BACKEND_URL}"
echo "DNS_RESOLVER: ${RESOLVER} (raw: ${RAW_RESOLVER})"
echo "=========================="

# Substitute environment variables in nginx config template
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Update resolver in generated config (replace 8.8.8.8 with actual resolver, keep ipv6=on)
sed -i "s|resolver 8.8.8.8 valid=300s ipv6=on;|resolver ${RESOLVER} valid=300s ipv6=on;|" /etc/nginx/conf.d/default.conf

# Verify the generated config
echo "=== Generated Nginx Config (proxy section) ==="
grep -A 5 "location /api/" /etc/nginx/conf.d/default.conf || true
echo "=== Generated Nginx Config (resolver) ==="
grep "resolver" /etc/nginx/conf.d/default.conf || true
echo "=============================================="

# Test DNS resolution (for debugging)
echo "=== Testing DNS Resolution ==="
echo "Testing: ${BACKEND_HOST}"
nslookup ${BACKEND_HOST} ${RAW_RESOLVER} 2>&1 || echo "nslookup failed or not available"
if [ "${BACKEND_HOST}" != "host.docker.internal" ]; then
    echo "Testing: ${BACKEND_HOST}.railway.internal"
    nslookup ${BACKEND_HOST}.railway.internal ${RAW_RESOLVER} 2>&1 || echo "nslookup failed or not available"
fi
echo "============================="

# Check if backend hostname contains dots (might be full domain)
if echo "${BACKEND_HOST}" | grep -q '\.' && [ "${BACKEND_HOST}" != "host.docker.internal" ]; then
    echo "WARNING: BACKEND_URL contains dots - might be using full domain instead of service name"
    echo "For Railway private networking, use service name only (e.g., 'bills' not 'bills.railway.internal')"
fi

# Start nginx (pid file is configured in nginx.conf to use /tmp/nginx.pid)
exec nginx -g 'daemon off;'
