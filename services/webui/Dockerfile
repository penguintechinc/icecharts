# Multi-stage build for IceCharts WebUI
# Stage 1: Dependencies
FROM node:20-bookworm-slim@sha256:1e85773c98c31d4fe5b545e4cb17379e617b348832fb3738b22a08f68dec30f3 AS dependencies

WORKDIR /app

# GitHub token for private package access
ARG GITHUB_TOKEN
RUN if [ -n "$GITHUB_TOKEN" ]; then \
      echo "@penguintechinc:registry=https://npm.pkg.github.com" > .npmrc && \
      echo "//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}" >> .npmrc; \
    fi

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev for testing)
RUN npm ci

# Stage 2: Lint
FROM dependencies AS lint

WORKDIR /app

# Copy source code
COPY . .

# Run linting
RUN npm run lint

# Stage 3: Test
FROM dependencies AS test

WORKDIR /app

# Copy source code and tests (test deps already installed via npm ci)
COPY . .

# Run tests
RUN npm run test -- --run --coverage

# Stage 4: Build
FROM dependencies AS builder

# Build arguments for Vite (production defaults)
ARG VITE_API_URL=""
ARG VITE_API_BASE_PATH="/api/v1"

WORKDIR /app

# Copy source code
COPY . .

# Build application with environment variables
# Production uses empty API_URL (relative paths) and /api/v1 base path
RUN VITE_API_URL="" VITE_API_BASE_PATH="/api/v1" npm run build

# Stage 5: Production
FROM nginx:stable-bookworm@sha256:552e7481ca93ffccd046aa658dbbed22caefbc09c66fa7cd247cbb90b8a5c609 AS production

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Remove default nginx config and default.conf
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Set permissions for non-root operation (k8s runs as UID 1000)
RUN chmod -R 755 /usr/share/nginx/html && \
    chmod -R 777 /etc/nginx/conf.d && \
    chmod -R 777 /var/log/nginx && \
    chmod -R 777 /var/cache/nginx && \
    mkdir -p /run && \
    chmod -R 777 /run && \
    mkdir -p /tmp/nginx && \
    chmod -R 777 /tmp/nginx

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run as non-root user
USER nginx

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
