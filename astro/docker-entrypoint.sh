#!/bin/sh
set -e

# Set default values if not provided
# For Railway: use private hostname with protocol and port
# Find service name in Railway: Backend service → Settings → Private Networking
# 
# Supported formats:
# - Short: http://bills:8000 (RECOMMENDED - uses Railway service discovery)
# - Full: http://bills.railway.internal:8000 (may not resolve with public DNS)
#
# IMPORTANT: Use the short format (just service name) for Railway private networking
# Railway's DNS is configured in /etc/resolv.conf and will be used automatically
BACKEND_URL=${BACKEND_URL:-http://backend:8000}
PORT=${PORT:-8080}

# Extract DNS resolver from /etc/resolv.conf (Railway configures this)
# Use the first nameserver found, or fallback to 8.8.8.8
DNS_RESOLVER=$(grep -E '^nameserver' /etc/resolv.conf | head -1 | awk '{print $2}' || echo "8.8.8.8")

# Add resolver to nginx.conf http block at runtime
# This must be done before nginx starts, and resolver must be in http block (not server block)
if ! grep -q "resolver.*valid" /etc/nginx/nginx.conf; then
    sed -i "/^http {/a\    resolver ${DNS_RESOLVER} valid=300s ipv6=off;" /etc/nginx/nginx.conf
fi

# Export variables for envsubst (envsubst only substitutes exported variables)
export BACKEND_URL
export PORT

# Substitute environment variables in nginx config template
# envsubst will replace ${PORT} and ${BACKEND_URL} with actual values
envsubst '${BACKEND_URL} ${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'

