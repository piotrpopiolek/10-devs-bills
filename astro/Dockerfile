# Build stage - Node.js environment for building Astro application
FROM node:20-alpine AS builder

ARG NODE_ENV=production
WORKDIR /app

# Copy package files for dependency caching
COPY astro/package.json astro/package-lock.json ./

# Install dependencies (including devDependencies needed for build)
RUN npm ci --only=production=false && \
    npm cache clean --force

# Copy application source code
COPY astro/ .

# Prepare for static build
# Remove API routes (not needed for static build)
RUN rm -rf src/pages/api && \
    # Disable middleware that uses Supabase (not needed for static build)
    mkdir -p src/middleware && \
    echo "import { defineMiddleware } from 'astro:middleware';" > src/middleware/index.ts && \
    echo "export const onRequest = defineMiddleware((context, next) => next());" >> src/middleware/index.ts && \
    # Fix tw-animate-css import
    if [ -f "src/styles/global.css" ]; then \
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
      fi; \
    fi

# Fix bills/[id].astro if it exists (change prerender to true for static build)
RUN if [ -f "src/pages/bills/[id].astro" ]; then \
      sed -i 's/export const prerender = false;/export const prerender = true;/' "src/pages/bills/[id].astro" && \
      awk '/export const prerender = true;/ { print; print "export async function getStaticPaths() { return []; }"; next }1' "src/pages/bills/[id].astro" > "src/pages/bills/[id].astro.tmp" && \
      mv "src/pages/bills/[id].astro.tmp" "src/pages/bills/[id].astro"; \
    fi

# Build Astro application
ARG PUBLIC_SITE_URL
ENV PUBLIC_SITE_URL=${PUBLIC_SITE_URL}
RUN npm run build

# Runtime stage - nginx for serving static files
FROM nginx:1.27-alpine

# Install gettext for envsubst and wget for healthcheck
RUN apk add --no-cache gettext wget

# Create non-root user
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user -g nginx nginx-user

WORKDIR /app

# Configure nginx to run as non-root user
RUN sed -i '/^user/d' /etc/nginx/nginx.conf && \
    sed -i 's|pid /var/run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Create nginx template directory
RUN mkdir -p /etc/nginx/templates

# Copy nginx configuration template and entrypoint script
COPY --from=builder /app/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=builder /app/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Set ownership
RUN mkdir -p /tmp && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d && \
    chown -R nginx-user:nginx-user /tmp && \
    chown -R nginx-user:nginx-user /etc/nginx/templates

# Switch to non-root user
USER nginx-user

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --spider --quiet "http://localhost:${PORT:-8080}/health" || exit 1

# Set environment variables
ENV PORT=8080

# Use entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
