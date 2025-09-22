# Project Overview

**ChattyCommander** is an advanced AI-powered voice command system with enterprise-grade security, monitoring, and performance optimizations. It listens continuously for voice commands using ONNX-based models, supports different states (idle, computer, chatty), and transitions between them based on detected wake words.

## Key Features

- Voice integration with wake word detection and transcription
- Multi-modal operation: CLI, Web API, WebSocket, GUI modes
- Real-time communication with WebSocket broadcasting
- AI agent integration with OpenAI Agents SDK
- Avatar system with 3D anime-style avatar and lip-sync
- Security: rate limiting, authentication, input validation
- Monitoring: health checks, metrics, performance monitoring

## Tech Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI with uvicorn
- **Voice Processing**: OpenWakeWord, ONNX models
- **AI**: OpenAI Agents SDK, MCP support
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis
- **Frontend**: Web UI with React (optional)
- **Testing**: pytest with coverage
- **Linting/Formatting**: ruff, black
- **Type Checking**: mypy
- **Security**: bandit, pip-audit
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## Architecture

- Modular FastAPI app with routers for core REST, avatar APIs, WS, agents
- Async processing throughout with asyncio
- Optional observability module with middleware and metrics
- CLI wrapper for configuration and command execution

## Development Workflow

1. Install dependencies: `uv sync`
1. Run tests: `make test`
1. Lint code: `make lint`
1. Format code: `make format-fix`
1. Start dev server: `make dev`
1. Commit changes (tests must pass)

## Entry Points

- CLI: `uv run chatty run`
- Web server: `uv run python main.py --web --no-auth`
- GUI: `uv run chatty gui`
- Orchestrator: `uv run python main.py --orchestrate --enable-text --web --no-auth`
