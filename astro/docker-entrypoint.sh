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

# Extract backend hostname for Host header (before any URL modifications)
# This will be used in nginx proxy_set_header Host
BACKEND_HOSTNAME=$(echo "${BACKEND_URL}" | sed -E 's|^https?://||' | sed -E 's|:.*$||' | sed -E 's|/.*$||')
# Always export BACKEND_HOSTNAME (nginx requires it)
export BACKEND_HOSTNAME

# Check if BACKEND_URL is a public Railway domain (should use HTTPS, not resolve to IP)
if echo "${BACKEND_URL}" | grep -qE '\.up\.railway\.app|\.railway\.app'; then
    echo "=== Detected Railway public domain ==="
    echo "Using public URL directly (no DNS resolution needed)"
    # Ensure HTTPS is used for public domains
    if echo "${BACKEND_URL}" | grep -qE '^http://'; then
        BACKEND_URL=$(echo "${BACKEND_URL}" | sed 's|^http://|https://|')
        export BACKEND_URL
        echo "✓ Updated BACKEND_URL to use HTTPS: ${BACKEND_URL}"
    fi
    # Remove port if it's 8000 (Railway public URLs use default HTTPS port 443)
    if echo "${BACKEND_URL}" | grep -qE ':8000'; then
        BACKEND_URL=$(echo "${BACKEND_URL}" | sed 's|:8000||')
        export BACKEND_URL
        echo "✓ Removed port 8000 (using default HTTPS port 443): ${BACKEND_URL}"
    fi
    # Update BACKEND_HOSTNAME after URL modifications
    BACKEND_HOSTNAME=$(echo "${BACKEND_URL}" | sed -E 's|^https?://||' | sed -E 's|:.*$||' | sed -E 's|/.*$||')
    export BACKEND_HOSTNAME
    echo "✓ Backend hostname for Host header: ${BACKEND_HOSTNAME}"
    echo "======================================"
# Try to resolve hostname to IP (works for Railway private networking and local Docker)
# This helps when nginx resolver doesn't work with hostnames
elif [ -n "${BACKEND_HOST}" ] && ! echo "${BACKEND_HOST}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
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
        # Keep original hostname for Host header (not IP)
        BACKEND_HOSTNAME="${BACKEND_HOST}"
        export BACKEND_HOSTNAME
        # Replace hostname with IP in BACKEND_URL for nginx config
        BACKEND_URL=$(echo "${BACKEND_URL}" | sed "s|${BACKEND_HOST}|${HOST_IP}|g")
        export BACKEND_URL
        echo "✓ Updated BACKEND_URL to use IP: ${BACKEND_URL}"
        echo "✓ Backend hostname for Host header: ${BACKEND_HOSTNAME}"
    else
        echo "✗ WARNING: Could not resolve ${BACKEND_HOST} to IP after ${MAX_RETRIES} attempts"
        echo "  Attempting fallback solutions..."
        # Keep original hostname for Host header
        BACKEND_HOSTNAME="${BACKEND_HOST}"
        export BACKEND_HOSTNAME
        
        # Fallback 1: Try using Railway public URL if available
        if [ -n "${RAILWAY_PUBLIC_DOMAIN}" ] && [ -n "${RAILWAY_SERVICE_NAME}" ]; then
            # Check if we're trying to connect to another Railway service
            if [ "${RAILWAY_SERVICE_NAME}" != "${BACKEND_HOST}" ]; then
                # Try to construct backend URL from Railway environment
                # Railway sets RAILWAY_<SERVICE_NAME>_URL for other services
                BACKEND_SERVICE_VAR=$(echo "${BACKEND_HOST}" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
                BACKEND_PUBLIC_URL=$(eval "echo \${RAILWAY_${BACKEND_SERVICE_VAR}_URL:-}")
                
                if [ -n "${BACKEND_PUBLIC_URL}" ]; then
                    echo "✓ Found Railway public URL for ${BACKEND_HOST}: ${BACKEND_PUBLIC_URL}"
                    BACKEND_URL="${BACKEND_PUBLIC_URL}"
                    export BACKEND_URL
                    echo "✓ Updated BACKEND_URL to use public URL: ${BACKEND_URL}"
                fi
            fi
        fi
        
        # Fallback 2: If still not resolved and BACKEND_PUBLIC_URL is set, use it
        if [ -z "${HOST_IP}" ] && [ -n "${BACKEND_PUBLIC_URL:-}" ]; then
            echo "✓ Using BACKEND_PUBLIC_URL fallback: ${BACKEND_PUBLIC_URL}"
            BACKEND_URL="${BACKEND_PUBLIC_URL}"
            export BACKEND_URL
        fi
        
        # Final check: if still using hostname, nginx will try to resolve at request time
        if echo "${BACKEND_URL}" | grep -q "${BACKEND_HOST}"; then
            echo "⚠ WARNING: Still using hostname ${BACKEND_HOST} in BACKEND_URL"
            echo "  Nginx will attempt DNS resolution at request time"
            echo "  This may fail if Railway DNS is not available"
            echo "  Solutions:"
            echo "    1. Use public backend URL: Set BACKEND_PUBLIC_URL=https://your-backend.up.railway.app"
            echo "    2. Verify backend service name in Railway Private Networking"
            echo "    3. Ensure backend service is running and in the same Railway project"
        fi
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
envsubst '${PORT} ${BACKEND_URL} ${BACKEND_HOSTNAME}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

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
