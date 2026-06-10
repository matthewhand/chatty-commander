# syntax=docker/dockerfile:1

# ================================
# Multi-stage Docker build for ChattyCommander
# ================================

# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

# Build-only system dependencies (never shipped in the final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# uv for fast, reproducible dependency installation
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install locked production dependencies into an isolated virtualenv.
# UV_PROJECT_ENVIRONMENT makes `uv sync` target /opt/venv instead of .venv;
# UV_COMPILE_BYTECODE precompiles .pyc so the runtime stage can run with a
# read-only filesystem (see docker-compose.yml) without losing startup speed.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ---- Stage 2: Runtime ----
FROM python:3.11-slim AS runtime

# Minimal runtime system dependencies.
# curl is required by the HEALTHCHECK below and by the docker-compose healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user
RUN groupadd -r -g 1000 chatty && \
    useradd -r -g chatty -u 1000 -m -d /home/chatty -s /usr/sbin/nologin chatty

WORKDIR /app

# Virtualenv with production dependencies only (no compilers, no dev tools)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Application source. Left root-owned (world-readable) on purpose: the app
# must not be able to modify its own code at runtime.
COPY src/ ./src/
COPY config.json config.json.example ./

# Writable directories are the only paths owned by the runtime user.
# models-* are wakeword model locations referenced by config.json; mount real
# models over them (see docker-compose.yml volumes).
RUN mkdir -p /app/logs /app/data /app/models /app/uploads \
        /app/models-idle /app/models-computer /app/models-chatty \
        /app/wakewords && \
    chown chatty:chatty /app/logs /app/data /app/models /app/uploads \
        /app/models-idle /app/models-computer /app/models-chatty \
        /app/wakewords && \
    # First-run default-config generation rewrites config.json in the workdir.
    chown chatty:chatty /app/config.json

USER chatty

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

EXPOSE 8000

# Start the web server on :8000 (same external behavior as before; the old
# CMD referenced /app/main.py, which never existed in the image).
CMD ["python", "-m", "chatty_commander.cli.main", "--web", "--no-auth", "--host", "0.0.0.0", "--port", "8000"]

# Metadata labels
ARG BUILD_DATE
ARG VCS_REF
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
