# ========================================
# Stage 1: Builder
# ========================================
FROM python:3.13-slim AS builder

LABEL maintainer="your-email@example.com"
LABEL description="Digitalism FastAPI Builder Stage"

# Set working directory
WORKDIR /build

# Install build dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# ========================================
# Stage 2: Runtime
# ========================================
FROM python:3.13-slim

LABEL maintainer="your-email@example.com"
LABEL description="Digitalism FastAPI Runtime Stage"

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create necessary directories
RUN mkdir -p /app/data /app/cache /app/logs && \
    chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser ./alembic.ini ./alembic.ini

# Copy entrypoint script
COPY --chown=appuser:appuser ./docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (runs all: migrations + etl + api)
CMD ["all"]
