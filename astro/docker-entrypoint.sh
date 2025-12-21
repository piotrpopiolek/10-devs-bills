#!/bin/sh
set -e

# Set default values
PORT=${PORT:-8080}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

# Export variables for envsubst
export PORT
export BACKEND_URL

# Add DNS resolver to nginx.conf for proxy_pass with variables
# Extract resolver from /etc/resolv.conf or use default
RESOLVER=$(grep -E '^nameserver' /etc/resolv.conf | head -1 | awk '{print $2}' || echo "8.8.8.8")
if ! grep -q "resolver.*valid" /etc/nginx/nginx.conf; then
    # Use /tmp for temporary file (nginx-user has write permissions there)
    awk -v resolver="${RESOLVER}" '/^http {/ { print; print "    resolver " resolver " valid=300s;"; next }1' /etc/nginx/nginx.conf > /tmp/nginx.conf.tmp && \
    cat /tmp/nginx.conf.tmp > /etc/nginx/nginx.conf && \
    rm -f /tmp/nginx.conf.tmp
fi

# Substitute environment variables in nginx config template
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx (pid file is configured in nginx.conf to use /tmp/nginx.pid)
exec nginx -g 'daemon off;'
