# Multi-arch Dockerfile for IceRuns Invoker (ARM64 + AMD64)
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install Python 3.13, Docker CLI, and build tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

RUN chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import redis; redis.from_url('redis://localhost:6379/0').ping()" || exit 1

# Run invoker
USER appuser
CMD ["python3", "-m", "app.invoker"]
