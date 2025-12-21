#!/bin/sh
set -e

# Set default values
PORT=${PORT:-8080}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

# Export variables for envsubst
export PORT
export BACKEND_URL

# Log configuration for debugging
echo "=== Nginx Configuration ==="
echo "PORT: ${PORT}"
echo "BACKEND_URL: ${BACKEND_URL}"
echo "=========================="

# Substitute environment variables in nginx config template
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Verify the generated config
echo "=== Generated Nginx Config (proxy section) ==="
grep -A 5 "location /api/" /etc/nginx/conf.d/default.conf || true
echo "=============================================="

# Start nginx (pid file is configured in nginx.conf to use /tmp/nginx.pid)
exec nginx -g 'daemon off;'
