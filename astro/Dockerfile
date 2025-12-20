# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code (after dependencies for better caching)
COPY . .

# Remove API routes before build (not needed in production - nginx proxies to backend)
# API routes have prerender=false which conflicts with static output
RUN rm -rf src/pages/api

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Create nginx templates directory
RUN mkdir -p /etc/nginx/templates

# Create nginx configuration template inline (to avoid file copy issues)
RUN echo 'server {' > /etc/nginx/templates/default.conf.template && \
    echo '    listen 80;' >> /etc/nginx/templates/default.conf.template && \
    echo '    server_name _;' >> /etc/nginx/templates/default.conf.template && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/templates/default.conf.template && \
    echo '    index index.html;' >> /etc/nginx/templates/default.conf.template && \
    echo '    gzip on;' >> /etc/nginx/templates/default.conf.template && \
    echo '    gzip_vary on;' >> /etc/nginx/templates/default.conf.template && \
    echo '    gzip_min_length 1024;' >> /etc/nginx/templates/default.conf.template && \
    echo '    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;' >> /etc/nginx/templates/default.conf.template && \
    echo '    add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/templates/default.conf.template && \
    echo '    add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/templates/default.conf.template && \
    echo '    add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/templates/default.conf.template && \
    echo '    location /api/ {' >> /etc/nginx/templates/default.conf.template && \
    echo '        rewrite ^/api/(.*)$ /api/v1/$1 break;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_pass ${BACKEND_URL};' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_http_version 1.1;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header Upgrade $http_upgrade;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header Connection '"'"'upgrade'"'"';' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header Host $host;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_cache_bypass $http_upgrade;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_connect_timeout 60s;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_send_timeout 60s;' >> /etc/nginx/templates/default.conf.template && \
    echo '        proxy_read_timeout 60s;' >> /etc/nginx/templates/default.conf.template && \
    echo '    }' >> /etc/nginx/templates/default.conf.template && \
    echo '    location / {' >> /etc/nginx/templates/default.conf.template && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/templates/default.conf.template && \
    echo '    }' >> /etc/nginx/templates/default.conf.template && \
    echo '    location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {' >> /etc/nginx/templates/default.conf.template && \
    echo '        expires 1y;' >> /etc/nginx/templates/default.conf.template && \
    echo '        add_header Cache-Control "public, immutable";' >> /etc/nginx/templates/default.conf.template && \
    echo '    }' >> /etc/nginx/templates/default.conf.template && \
    echo '    location /health {' >> /etc/nginx/templates/default.conf.template && \
    echo '        access_log off;' >> /etc/nginx/templates/default.conf.template && \
    echo '        return 200 "healthy\\n";' >> /etc/nginx/templates/default.conf.template && \
    echo '        add_header Content-Type text/plain;' >> /etc/nginx/templates/default.conf.template && \
    echo '    }' >> /etc/nginx/templates/default.conf.template && \
    echo '}' >> /etc/nginx/templates/default.conf.template

# Create entrypoint script inline (to avoid file copy issues)
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo 'BACKEND_URL=${BACKEND_URL:-http://backend:8000}' >> /docker-entrypoint.sh && \
    echo 'envsubst '"'"'${BACKEND_URL}'"'"' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g '"'"'daemon off;'"'"'' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Copy built files from builder stage (after copying config files)
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]

