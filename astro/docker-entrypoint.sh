#!/bin/sh
set -e

# Set default values
PORT=${PORT:-8080}
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

# Export variables for envsubst
export PORT
export BACKEND_URL

# Substitute environment variables in nginx config template
envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx (pid file is configured in nginx.conf to use /tmp/nginx.pid)
exec nginx -g 'daemon off;'
