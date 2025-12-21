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

# Export variables for envsubst (envsubst only substitutes exported variables)
export BACKEND_URL
export PORT
export DNS_RESOLVER

# Substitute environment variables in nginx config template
# envsubst will replace ${PORT}, ${BACKEND_URL}, and ${DNS_RESOLVER} with actual values
envsubst '${BACKEND_URL} ${PORT} ${DNS_RESOLVER}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'

