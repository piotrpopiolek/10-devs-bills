# Build stage - Node.js environment for building Astro application
FROM node:20-alpine AS builder

# Set build arguments
ARG NODE_ENV=production

# Set working directory
WORKDIR /app

# Install build dependencies (gettext for envsubst)
RUN apk add --no-cache gettext

# Copy package files first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies (including devDependencies needed for build)
# tw-animate-css is in devDependencies but needed for CSS build
RUN npm ci --only=production=false && \
    npm cache clean --force

# Copy application source code
COPY . .

# Remove API routes directory (not needed for static build, handled by nginx proxy)
# This prevents Astro from requiring an adapter for server-rendered routes
RUN rm -rf src/pages/api && \
    # Disable middleware that uses Supabase (not needed for static build)
    # Create middleware directory if it doesn't exist, then create an empty middleware that just passes through
    mkdir -p src/middleware && \
    echo "import { defineMiddleware } from 'astro:middleware';" > src/middleware/index.ts && \
    echo "export const onRequest = defineMiddleware((context, next) => next());" >> src/middleware/index.ts && \
    # Fix tw-animate-css import - use node_modules path for proper resolution
    # Check if package exists and use appropriate import path
    if [ -d "node_modules/tw-animate-css" ]; then \
      if [ -f "node_modules/tw-animate-css/index.css" ]; then \
        sed -i 's|@import "tw-animate-css";|@import "../node_modules/tw-animate-css/index.css";|' src/styles/global.css; \
      elif [ -f "node_modules/tw-animate-css/dist/index.css" ]; then \
        sed -i 's|@import "tw-animate-css";|@import "../node_modules/tw-animate-css/dist/index.css";|' src/styles/global.css; \
      else \
        sed -i 's|@import "tw-animate-css";|/* @import "tw-animate-css"; */|' src/styles/global.css; \
      fi; \
    else \
      sed -i 's|@import "tw-animate-css";|/* @import "tw-animate-css"; */|' src/styles/global.css; \
    fi

# Fix bills/[id].astro: change prerender = false to true and add getStaticPaths
# This allows static build - the page will be handled client-side via React
RUN if [ -f "src/pages/bills/[id].astro" ]; then \
    sed -i 's/export const prerender = false;/export const prerender = true;/' "src/pages/bills/[id].astro" && \
    awk '/export const prerender = true;/ { print; print "export async function getStaticPaths() { return []; }"; next }1' "src/pages/bills/[id].astro" > "src/pages/bills/[id].astro.tmp" && \
    mv "src/pages/bills/[id].astro.tmp" "src/pages/bills/[id].astro"; \
    fi

# Build Astro application (outputs to dist/)
RUN npm run build

# Runtime stage - nginx for serving static files
FROM nginx:1.27-alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user -g nginx nginx-user

# Set working directory
WORKDIR /app

# Create nginx template directory
RUN mkdir -p /etc/nginx/templates

# Configure nginx to run as non-root user
# Modify main nginx.conf to set user and pid file location
RUN sed -i 's/^user.*/user nginx-user;/' /etc/nginx/nginx.conf && \
    sed -i 's|pid /var/run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Copy nginx configuration template and entrypoint script from builder stage
# (These files are copied in builder stage with COPY . ., so they're available there)
COPY --from=builder /app/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=builder /app/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy built static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create healthcheck script (HEALTHCHECK doesn't support env var substitution)
RUN echo '#!/bin/sh\nPORT=${PORT:-8080}\nwget --spider --quiet "http://localhost:${PORT}/health" || exit 1' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Set ownership of nginx directories and create necessary directories
RUN mkdir -p /tmp && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d && \
    chown -R nginx-user:nginx-user /run && \
    chown -R nginx-user:nginx-user /tmp && \
    chown -R nginx-user:nginx-user /etc/nginx/templates

# Switch to non-root user
USER nginx-user

# Expose port (default 8080, configurable via PORT env var)
EXPOSE 8080

# Health check (script handles PORT env var)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Set environment variables with defaults
ENV PORT=8080
ENV BACKEND_URL=http://backend:8000

# Use entrypoint script to configure nginx and start server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

