# Multi-stage build for ChattyCommander
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r chatty && useradd -r -g chatty chatty

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/logs && chown -R chatty:chatty /app

# Switch to non-root user
USER chatty

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8100/api/v1/status || exit 1

# Expose port
EXPOSE 8100

# Default command
CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "8100"]
