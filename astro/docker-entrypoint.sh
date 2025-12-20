#!/bin/sh
set -e

# Set default values if not provided
BACKEND_URL=${BACKEND_URL:-http://backend:8000}
PORT=${PORT:-8080}

# Export variables for envsubst (envsubst only substitutes exported variables)
export BACKEND_URL
export PORT

# Substitute environment variables in nginx config template
# envsubst will replace ${PORT} and ${BACKEND_URL} with actual values
envsubst '${BACKEND_URL} ${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'

