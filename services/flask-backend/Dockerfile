# IceCharts Flask API Dockerfile
# Multi-stage build with debian-slim base for optimal size and security
# Python 3.13 for performance optimizations (dataclasses with slots, asyncio)

# Builder stage
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Test stage
FROM builder AS test

WORKDIR /build

# Install testing dependencies
RUN pip install --user --no-cache-dir \
    pytest==8.3.4 \
    pytest-cov==6.0.0 \
    pytest-mock==3.13.0

# Copy test files and app code
COPY . .

# Set test environment
ENV FLASK_ENV=testing
ENV TESTING=true
ENV DB_TYPE=sqlite
ENV DATABASE_URL="sqlite:///:memory:"
ENV JWT_SECRET_KEY=test-secret-key
ENV SECRET_KEY=test-secret-key

# Run tests with coverage
RUN python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-summary -v

# Lint stage
FROM builder AS lint

WORKDIR /build

# Install linting tools
RUN pip install --user --no-cache-dir \
    black==24.10.0 \
    flake8==7.1.1 \
    mypy==1.14.0 \
    isort==5.13.2

# Copy source code
COPY . .

# Run linting
RUN flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics && \
    black --check app/ tests/ && \
    isort --check-only app/ tests/ && \
    mypy app/ --ignore-missing-imports || true

# Runtime stage
FROM python:3.13-slim

# Build arguments for JWT token expiration
ARG JWT_ACCESS_TOKEN_HOURS=4
ARG JWT_REFRESH_TOKEN_DAYS=30

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 icecharts

# Copy Python dependencies from builder to icecharts user
COPY --from=builder /root/.local /home/icecharts/.local
RUN chown -R icecharts:icecharts /home/icecharts/.local

# Create instance directory for PyDAL migrations (before switching to icecharts user)
RUN mkdir -p /app/instance && chown -R icecharts:icecharts /app/instance

# Switch to non-root user
USER icecharts

# Make sure scripts in .local are usable
ENV PATH=/home/icecharts/.local/bin:$PATH

# Copy application code
COPY --chown=icecharts:icecharts app /app/app
COPY --chown=icecharts:icecharts requirements.txt /app/

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

# Set environment variables
ENV FLASK_APP=app.main:create_app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV JWT_ACCESS_TOKEN_HOURS=${JWT_ACCESS_TOKEN_HOURS}
ENV JWT_REFRESH_TOKEN_DAYS=${JWT_REFRESH_TOKEN_DAYS}

# Run application with uvicorn ASGI server for async Flask support
CMD ["uvicorn", \
     "app.main:create_app", \
     "--factory", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "h11", \
     "--access-log", \
     "--log-level", "info"]
