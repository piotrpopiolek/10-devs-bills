#!/bin/sh
set -e

# Set default port
PORT=${PORT:-8080}

# Export variable for envsubst
export PORT

# Substitute environment variables in nginx config template
envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx (pid file is configured in nginx.conf to use /tmp/nginx.pid)
exec nginx -g 'daemon off; pid /tmp/nginx.pid;'
