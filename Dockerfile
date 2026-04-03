# ================================
# Multi-stage Docker build for ChattyCommander
# ================================

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies (production only)
RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    # Audio/video processing dependencies
    libasound2-dev \
    libportaudio2 \
    alsa-utils \
    pulseaudio-utils \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # System monitoring
    procps \
    htop \
    # Security and SSL
    openssl \
    ca-certificates \
    curl \
    wget \
    # Timezone data
    tzdata \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r -g 1000 chatty && \
    useradd -r -g chatty -u 1000 -m -d /home/chatty -s /bin/bash chatty && \
    mkdir -p /home/chatty && \
    chown -R chatty:chatty /home/chatty

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with proper ownership
COPY --chown=chatty:chatty . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/models /app/uploads && \
    chown -R chatty:chatty /app && \
    chmod -R 755 /app

# Switch to non-root user
USER chatty

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Health check with comprehensive endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command with production settings
CMD ["python", "main.py", "--web", "--no-auth", "--host", "0.0.0.0", "--port", "8000"]

# Metadata labels
LABEL org.opencontainers.image.title="ChattyCommander" \
      org.opencontainers.image.description="Advanced AI-powered voice command system with web interface" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.authors="ChattyCommander Team <team@chattycommander.dev>" \
      org.opencontainers.image.source="https://github.com/matthewhand/chatty-commander" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="ChattyCommander" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      security.scan.target="python:3.11-slim"
