#!/bin/sh
set -e

# Set default values if not provided
# For Railway: use private hostname with protocol and port
# 
# RECOMMENDED: Use Railway Reference Variables in Railway Dashboard:
#   BACKEND_URL=http://${{bills.RAILWAY_PRIVATE_DOMAIN}}:${{bills.PORT}}
#   (Replace 'bills' with your backend service name)
#   Note: PORT must be set as a service variable in backend service
#
# ALTERNATIVE: Hardcoded values (if reference variables don't work):
#   - Short: http://bills:8000 (uses Railway service discovery)
#   - Full: http://bills.railway.internal:8000
#
# Railway's DNS is configured in /etc/resolv.conf and will be used automatically
# Check if BACKEND_URL is empty or contains unresolved reference variables
if [ -z "${BACKEND_URL}" ] || echo "${BACKEND_URL}" | grep -q '\${{'; then
    echo "WARNING: BACKEND_URL is empty or contains unresolved reference variables!"
    echo "BACKEND_URL value: '${BACKEND_URL}'"
    echo "Falling back to default: http://backend:8000"
    BACKEND_URL="http://backend:8000"
fi
BACKEND_URL=${BACKEND_URL:-http://backend:8000}
PORT=${PORT:-8080}

# Extract DNS resolver from /etc/resolv.conf (Railway configures this)
# Use the first nameserver found, or fallback to 8.8.8.8
DNS_RESOLVER=$(grep -E '^nameserver' /etc/resolv.conf | head -1 | awk '{print $2}' || echo "8.8.8.8")

# Add resolver to nginx.conf http block at runtime
# This must be done before nginx starts, and resolver must be in http block (not server block)
# Railway supports both IPv4 and IPv6 in new environments (after Oct 16, 2025)
# Use awk to modify and write directly, then copy over original file
if ! grep -q "resolver.*valid" /etc/nginx/nginx.conf; then
    # Enable IPv6 support for Railway's dual-stack networking
    # Escape curly braces in awk pattern - use /^http \{/ instead of /^http {/
    awk -v resolver="${DNS_RESOLVER}" '/^http \{/ { print; print "    resolver " resolver " valid=300s ipv6=on;"; next }1' /etc/nginx/nginx.conf > /tmp/nginx.conf.tmp && \
    # Copy temp file over original (cp preserves permissions better than mv)
    cp /tmp/nginx.conf.tmp /etc/nginx/nginx.conf && \
    rm -f /tmp/nginx.conf.tmp
fi

# Export variables for envsubst (envsubst only substitutes exported variables)
export BACKEND_URL
export PORT

# Log configuration for debugging
echo "=== Nginx Configuration ==="
echo "PORT: ${PORT}"
echo "BACKEND_URL: ${BACKEND_URL}"
echo "DNS_RESOLVER: ${DNS_RESOLVER}"
echo "=========================="

# Substitute environment variables in nginx config template
# envsubst will replace ${PORT} and ${BACKEND_URL} with actual values
envsubst '${BACKEND_URL} ${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Verify the generated config (show backend hostname extraction)
echo "=== Generated Nginx Config (backend hostname) ==="
grep -A 5 "location /api/" /etc/nginx/conf.d/default.conf | head -10 || true
echo "=================================================="

# Start nginx
exec nginx -g 'daemon off;'

