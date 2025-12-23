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

# Try to resolve hostname to IP (works for Railway and local Docker)
# This helps when nginx resolver doesn't work with hostnames
if [ -n "${BACKEND_HOST}" ] && ! echo "${BACKEND_HOST}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    # Not an IP address, try to resolve it
    echo "=== Resolving hostname: ${BACKEND_HOST} ==="
    
    # Try multiple resolution methods with retries (DNS may not be ready immediately)
    HOST_IP=""
    MAX_RETRIES=5
    RETRY_DELAY=2
    
    for attempt in $(seq 1 ${MAX_RETRIES}); do
        echo "Attempt ${attempt}/${MAX_RETRIES} to resolve ${BACKEND_HOST}..."
        
        # Method 1: Try getent hosts (works in Docker networks)
        HOST_IP=$(getent hosts "${BACKEND_HOST}" 2>/dev/null | awk '{print $1}' | head -1)
        if [ -n "${HOST_IP}" ]; then
            echo "✓ Resolved ${BACKEND_HOST} to IP: ${HOST_IP} (via getent)"
            break
        fi
        
        # Method 2: Try with .railway.internal suffix (Railway specific)
        HOST_IP=$(getent hosts "${BACKEND_HOST}.railway.internal" 2>/dev/null | awk '{print $1}' | head -1)
        if [ -n "${HOST_IP}" ]; then
            echo "✓ Resolved ${BACKEND_HOST}.railway.internal to IP: ${HOST_IP} (via getent)"
            break
        fi
        
        # Method 3: Try nslookup as fallback
        if command -v nslookup >/dev/null 2>&1; then
            HOST_IP=$(nslookup "${BACKEND_HOST}" ${RAW_RESOLVER} 2>/dev/null | grep -A 1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
            if [ -n "${HOST_IP}" ]; then
                echo "✓ Resolved ${BACKEND_HOST} to IP: ${HOST_IP} (via nslookup)"
                break
            fi
        fi
        
        # If not resolved, wait before retry
        if [ ${attempt} -lt ${MAX_RETRIES} ]; then
            echo "  Waiting ${RETRY_DELAY}s before retry..."
            sleep ${RETRY_DELAY}
        fi
    done
    
    # If we got an IP, replace hostname with IP in BACKEND_URL
    if [ -n "${HOST_IP}" ]; then
        echo "✓ Successfully resolved ${BACKEND_HOST} to IP: ${HOST_IP}"
        # Replace hostname with IP in BACKEND_URL for nginx config
        BACKEND_URL=$(echo "${BACKEND_URL}" | sed "s|${BACKEND_HOST}|${HOST_IP}|g")
        export BACKEND_URL
        echo "✓ Updated BACKEND_URL to use IP: ${BACKEND_URL}"
    else
        echo "✗ ERROR: Could not resolve ${BACKEND_HOST} to IP after ${MAX_RETRIES} attempts"
        echo "  This will cause nginx to fail when proxying requests"
        echo "  Please check:"
        echo "    1. BACKEND_URL is set correctly: ${BACKEND_URL}"
        echo "    2. Backend service is running and accessible"
        echo "    3. Service name matches Railway Private Networking name"
        echo "  Nginx will still start, but API requests will fail!"
    fi
    echo "=========================================="
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
