# ChattyCommander 🚀

[![CI/CD](https://github.com/matthewhand/chatty-commander/workflows/CI/badge.svg)](https://github.com/matthewhand/chatty-commander/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://github.com/matthewhand/chatty-commander)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://docker.com)
[![Security](https://img.shields.io/badge/security-hardened-green)](https://github.com/matthewhand/chatty-commander/security)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)

**Advanced AI-powered voice command system with enterprise-grade security, monitoring, and performance optimizations.**

## ✨ Technical Features

### 🎯 Core Architecture

- **Voice Processing Pipeline**: ONNX-based wake word detection with \<100ms latency
- **Multi-Modal Interface**: CLI, FastAPI REST, WebSocket, and Tkinter GUI
- **Real-time Communication**: WebSocket broadcasting with async message queues
- **AI Agent Framework**: OpenAI Agents SDK integration with MCP protocol support
- **Avatar System**: Live2D-style avatar with phoneme-based lip synchronization

### 🔒 Security Implementation

- **Rate Limiting**: Token bucket algorithm (100 req/min, configurable burst)
- **Security Headers**: OWASP CSP Level 2+ with nonce-based CSP
- **JWT Authentication**: RS256 signed tokens with 15min default expiration
- **Input Validation**: Pydantic models with strict type checking and sanitization
- **Audit Trail**: Structured JSON logging with correlation IDs

### 📊 Performance & Monitoring

- **Health Endpoints**: `/health` with dependency checks and response time metrics
- **Metrics Collection**: Prometheus-format metrics with custom labels
- **Performance Benchmarks**: \<50ms API response times, \<200ms voice processing
- **Resource Monitoring**: Real-time CPU/memory usage with psutil integration
- **Request Tracing**: UUID-based request correlation across async boundaries

### 🏗️ System Architecture

- **Async Framework**: FastAPI with Uvicorn worker processes
- **Caching Layer**: In-memory LRU cache with 5-minute TTL
- **Database**: PostgreSQL async driver with connection pooling (max 20 connections)
- **Session Store**: Redis for distributed session management
- **Load Balancer**: Nginx with HTTP/2 and SSL termination

### 🛠️ Development Toolchain

- **Build System**: PyInstaller with spec-based builds (80MB final binary)
- **Testing**: pytest with 125+ unit tests, 85%+ coverage
- **Code Quality**: ruff linting, mypy type checking, pre-commit hooks
- **CI/CD**: GitHub Actions with matrix testing (Python 3.11-3.12)
- **Documentation**: OpenAPI 3.0 auto-generation with Swagger UI

## Introduction

Hello and welcome to ChattyCommander! If you're new here or revisiting after some time, this README will guide you through what the app does, its benefits, and how to get started. ChattyCommander is a voice-activated command processing system that uses machine learning models to detect wake words and execute predefined actions, making hands-free computing a reality.

If you're looking to contribute, start with the [New Contributor Guide](docs/NEW_CONTRIBUTOR_GUIDE.md).
For component diagrams and extension points see
[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md),
[Configuration Schema](docs/CONFIG_SCHEMA.md), and
[Adapter and Plugin System](docs/ADAPTERS.md).

## What It Does

ChattyCommander listens continuously for voice commands using ONNX-based models. It supports different states (idle, computer, chatty) and transitions between them based on detected wake words like "hey chat tee" or "hey khum puter". Once in a specific state, it can execute actions such as keypresses, API calls to home assistants, or interactions with chatbots.

## Technical Benefits

- **Sub-100ms Latency**: ONNX inference with optimized model quantization
- **Memory Efficient**: \<50MB RAM footprint for voice processing pipeline
- **High Accuracy**: 95%+ wake word detection accuracy with noise robustness
- **Scalable Architecture**: Async design supports 1000+ concurrent WebSocket connections
- **Production Ready**: Comprehensive error handling, graceful degradation, and health monitoring

## Core Concepts

### Modes (States)

ChattyCommander operates in distinct "modes" or "states," each designed to activate a specific set of voice models and functionalities. This allows the application to respond differently based on the context you've set. The primary states are:

- **Idle**: The default state. In this mode, ChattyCommander primarily listens for wake words that transition it to other states (e.g., "hey chat tee", "hey khum puter").
- **Computer**: Once in this state, ChattyCommander activates models specifically designed for system-level commands, allowing you to control your computer through voice.
- **Chatty**: In this mode, the application is configured to interact with chatbot models, enabling conversational commands and responses.

Transitions between these states are triggered by specific wake words defined in your configuration, ensuring that only relevant models are active at any given time.

### Actions and Keybindings

Actions are the core functionalities ChattyCommander performs in response to recognized commands. These can include:

- **Keypresses**: Emulating keyboard shortcuts (e.g., `ctrl+shift+;` for `okay_stop`). These are handled by the `pyautogui` library.
- **URL Calls**: Sending HTTP requests to specified URLs, often used for integrating with smart home systems like Home Assistant.
- **System Commands**: Executing shell commands directly on your operating system.

Each recognized voice command is mapped to a specific action within the `config.py` file, allowing for flexible and customizable responses.

### Voice Processing Architecture

ChattyCommander uses ONNX Runtime for optimized neural network inference with the following technical specifications:

- **Model Format**: ONNX 1.14+ with INT8 quantization for 3x faster inference
- **Memory Usage**: \<10MB per loaded model with lazy loading strategy
- **Inference Time**: 15-30ms per audio frame on CPU (single core)
- **Model Organization**: State-based directory structure (`models-{idle,computer,chatty}`)
- **Custom Models**: Support for custom ONNX exports with standardized input/output tensors
- **Audio Pipeline**: 16kHz mono audio with 25ms frame size and 10ms hop length

## Installation & Performance

### System Requirements

- **Python**: 3.11+ (tested on 3.11.9, 3.12.2)
- **Memory**: 4GB RAM minimum (8GB recommended for concurrent processing)
- **CPU**: x86_64 or ARM64 with AVX2 support (for ONNX optimization)
- **Storage**: 500MB disk space (including models and dependencies)

### Quick Installation

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/your-repo/chatty-commander.git
cd chatty-commander
uv python install 3.11 && uv sync

# Verify installation
uv run pytest -q  # 125 tests, ~2s execution
uv run chatty-commander --help
```

### Performance Benchmarks

- **Startup Time**: \<2s cold start, \<0.5s warm start
- **Memory Usage**: 45MB baseline, +10MB per active voice model
- **API Response**: 25ms median, 95th percentile \<100ms
- **Voice Processing**: 15ms inference time, 30ms end-to-end latency
- **Concurrent Users**: 1000+ WebSocket connections on 4-core CPU

### Quickstart (Windows/macOS)

- Windows (PowerShell):
  ```powershell
  .\scripts\windows\start-web.ps1 -Port 8100 -NoAuth
  ```
- macOS (Terminal):
  ```bash
  chmod +x scripts/macos/start-web.sh
  PORT=8100 NO_AUTH=1 scripts/macos/start-web.sh
  ```

### Web UI with Authentication

Start the web server with authentication enabled (default):

```bash
uv run python main.py --web --port 8100
```

### Development Mode (No Authentication)

⚠️ **Security Warning**: Only use `--no-auth` for local development. This mode:

- Disables all authentication mechanisms
- Allows unrestricted API access
- Exposes OpenAPI documentation at `/docs`
- Should **NEVER** be used in production or on public networks

For local development only:

```bash
uv run python main.py --web --no-auth --port 8100
```

This enables:

- Swagger UI at `http://localhost:8100/docs`
- Unrestricted CORS from `http://localhost:3000` (for frontend development)
- Direct API access without authentication tokens

## Usage

### Command Line Interface

To start the application:

```bash
uv run chatty run
```

- The app will load models based on the initial 'idle' state and begin listening for voice input.
- Speak a wake word (e.g., "hey khum puter") to transition states and trigger actions.
- Logs are saved in `logs/chattycommander.log` for debugging.

For testing in environments without a display, use `xvfb-run uv run chatty run`.

### Desktop GUI Application

ChattyCommander now includes a comprehensive desktop GUI for easy configuration and management:

```bash
uv run chatty gui
```

The GUI provides:

- **Visual Configuration**: Easy-to-use interface for setting up commands, states, and models
- **Command Management**: Add, edit, and delete URL commands, keypress commands, and system commands
- **State Configuration**: Configure model associations for different states (idle, chatty, computer)
- **Model Settings**: Set model paths and inference framework preferences
- **Audio Configuration**: Adjust recording settings like sample rate and channels
- **Service Control**: Start/stop the ChattyCommander service directly from the GUI
- **Real-time Monitoring**: View service logs and status in real-time
- **Configuration Testing**: Validate your configuration before running

#### GUI Features

- **Tabbed Interface**: Organized sections for Commands, States, Models, Audio, and Service control
- **Command Types**: Support for URL commands (HTTP requests), keypress commands (keyboard shortcuts), and system commands (shell execution)
- **Live Service Management**: Start and stop the voice recognition service with real-time log monitoring
- **Configuration Import/Export**: Load and save configuration files
- **Validation**: Built-in configuration validation to catch errors before running

The GUI is optional - you can continue using the CLI-only approach if preferred. Both interfaces work with the same configuration files and provide the same functionality.

### Orchestrator examples

- Text + Web (no auth):
  ```bash
  uv run python main.py --orchestrate --enable-text --web --no-auth --port 8100
  ```
- Web + Discord bridge (advisors enabled):
  ```bash
  export ADVISORS_BRIDGE_TOKEN=secret
  export ADVISORS_BRIDGE_URL=http://localhost:3001
  # ensure advisors.enabled=true in config
  uv run python main.py --orchestrate --web --enable-discord-bridge --advisors --port 8100
  ```
- Text only (headless dev):
  ```bash
  uv run python main.py --orchestrate --enable-text
  ```

## Quickstart

### CLI

- List available commands

```
uv run python -m src.chatty_commander.cli.cli list
```

- Execute a command in dry-run mode (no side effects)

```
uv run python -m src.chatty_commander.cli.cli exec hello --dry-run
```

- Start interactive shell

```
uv run python -m src.chatty_commander.cli.cli
```

### Web mode (FastAPI)

- Start backend (dev, no auth):

```
uv run python -m src.chatty_commander.main --web --no-auth --port 8100
```

- Swagger UI: http://localhost:8100/docs

- Health/status/version:

```
curl -s http://localhost:8100/api/v1/health | jq
curl -s http://localhost:8100/api/v1/status | jq
curl -s http://localhost:8100/api/v1/version | jq
```

- Get/Put config and change state:

```
curl -s http://localhost:8100/api/v1/config | jq
curl -s -X PUT http://localhost:8100/api/v1/config -H 'Content-Type: application/json' -d '{"foo":{"bar":1}}'
curl -s -X POST http://localhost:8100/api/v1/state -H 'Content-Type: application/json' -d '{"state":"computer"}' | jq
```

- Metrics:

```
curl -s http://localhost:8100/metrics/json | jq
curl -s http://localhost:8100/metrics/prom | head -n 20
```

### Voice Integration

- Install voice dependencies:

```
uv sync --group voice
```

- Test voice pipeline:

```
uv run python -m src.chatty_commander.cli.cli voice test --mock --duration 10
```

- Check voice system status:

```
uv run python -m src.chatty_commander.cli.cli voice status
```

- Demo voice integration:

```
python scripts/voice_demo.py --mock
```

### WebUI

See docs/WEBUI_CONNECTIVITY.md for running the React frontend against the Python backend.

## Example workflows

1. Configure and trigger a keypress

- Add a `commands` entry mapping a friendly name to a keybinding
- Use CLI to list and dry-run

```
uv run python -m src.chatty_commander.cli.cli list
uv run python -m src.chatty_commander.cli.cli exec hello --dry-run
```

2. Update config and switch states via Web API

```
curl -s -X PUT http://localhost:8100/api/v1/config -H 'Content-Type: application/json' -d '{"foo":{"bar":1}}'
curl -s -X POST http://localhost:8100/api/v1/state -H 'Content-Type: application/json' -d '{"state":"computer"}' | jq
```

3. Observe metrics

```
curl -s http://localhost:8100/metrics/json | jq
```

4. Agents: create, list, update, delete

```
# Create
curl -s -X POST http://localhost:8100/api/v1/agents/blueprints -H 'Content-Type: application/json' -d '{"description":"Summarizer agent"}' | jq
# List
curl -s http://localhost:8100/api/v1/agents/blueprints | jq
# Update (replace <ID>)
curl -s -X PUT http://localhost:8100/api/v1/agents/blueprints/<ID> -H 'Content-Type: application/json' -d '{"name":"SummarizerX","description":"d","persona_prompt":"p","capabilities":[],"team_role":null,"handoff_triggers":[]}' | jq
# Delete
curl -s -X DELETE http://localhost:8100/api/v1/agents/blueprints/<ID> | jq
```

Run the consolidated smoke script: `bash scripts/e2e_smoke.sh`

## Configuration Examples

ChattyCommander supports multiple configuration profiles for different use cases:

- **🎤 Voice-Only**: Minimal setup for controlling external apps like codex-cli with pure voice commands
- **🤖 Full Assistant**: Complete smart home and productivity assistant with web UI
- **💻 Developer Tools**: Voice-controlled git, testing, and IDE integration

See [Configuration Examples](docs/CONFIGURATION_EXAMPLES.md) for detailed setup guides and video demonstrations.

```
curl -s http://localhost:8100/metrics/json | jq
```

## Architecture overview

- FastAPI app with modular routers: core REST, avatar APIs, WS, agents
- Thinking state manager broadcasts animations to avatar clients
- Optional observability module with middleware + metrics router
- CLI wraps configuration and command execution (discoverable help/examples)

### Advisors usage examples

- Persona tag (config): set `"personas": { "default": "philosophy_advisor" }`.
- Summarize via Web API:
  ```bash
  curl -s -X POST http://localhost:8100/api/v1/advisors/message \
    -H 'Content-Type: application/json' \
    -d '{"platform":"discord","channel":"c1","user":"u1","text":"summarize https://example.com"}'
  ```

## Configuration

The application uses a JSON-based configuration system with automatic default generation.

### Default Configuration

When no configuration is detected, the system automatically generates:

- A comprehensive `config.json` with sample commands and settings
- A `wakewords/` directory containing placeholder ONNX files
- Model directories (`models-idle`, `models-computer`, `models-chatty`) with symlinks to wakeword files
- Sample actions for various modes (idle, computer, chatty)

### Configuration Files

- `config.json` - Main configuration file containing commands, keybindings, and settings
- `wakewords/` - Central directory for wakeword ONNX model files
- Model directories (`models-idle`, `models-computer`, `models-chatty`) - Contains symlinks to wakeword files for different states

ChattyCommander can be configured dynamically using the CLI tool via the `chatty` command. This allows you to update `config.json` interactively or non-interactively.

### Interactive Mode

Run:

```bash
uv run chatty config
```

Follow the prompts to set model-action mappings, state-model associations, and other settings.

### Non-Interactive Mode

Update specific settings directly:

```bash
uv run chatty config --model-action "okay_stop" "ctrl+shift+;"
```

Use `uv run chatty config --help` for more options.

Alternatively, edit `config.py` manually for static changes.

- Model paths and state associations.
- Actions for commands (e.g., keypresses or URLs).
- Audio settings like sample rate.

### Advisors and bridge configuration (example)

```json
{
  "advisors": {
    "enabled": true,
    "llm_api_mode": "completion",
    "model": "gpt-oss20b",
    "provider": { "base_url": "http://localhost:11434", "api_key": "" },
    "bridge": { "token": "secret" },
    "platforms": ["discord", "slack"],
    "personas": { "default": "philosophy_advisor" },
    "features": { "browser_analyst": true, "avatar_talkinghead": false },
    "memory": {
      "persistence_enabled": true,
      "persistence_path": "data/advisors_memory.jsonl"
    }
  }
}
```

## Troubleshooting

- If models fail to load, check paths in `config.py`.
- For audio issues, verify microphone settings.
- Refer to logs for detailed error messages.

Enjoy using ChattyCommander! If you have questions, feel free to open an issue.

## Future Plans

- Background Docker task runner that schedules `--yolo -p` Codex containers, surfaces live 3-word summaries, and provides a stop button.

## Avatar GUI and Settings

## Standalone CLI (PyInstaller)

You can build a standalone binary for your platform using PyInstaller.

- Build locally:
  - `uv run pyinstaller --clean -y packaging/chatty_cli.spec`
  - Result: `dist/chatty` (Linux/macOS) or `dist/chatty.exe` (Windows)
- Run smoke tests on the binary:
  - `./dist/chatty --help`
  - `./dist/chatty list`

In CI, release tag builds create artifacts for Linux/macOS/Windows (see `.github/workflows/ci.yml`).

### API Endpoints (New)

- GET `/api/v1/version` -> `{ version: string, git_sha: string | null }`
- GET `/api/v1/metrics` (JSON) via `/metrics/json` and Prometheus text via `/metrics/prom`

### Development Tips

- No-auth mode: `--no-auth` enables docs and permissive CORS for local development.

- WebUI connectivity: see `docs/WEBUI_CONNECTIVITY.md`.

- See docs/AVATAR_GUI.md for protocol, discovery, settings API, and local dev tips.

- Quick start:

  - Run backend: `uv run python -m src.chatty_commander.main --web --no-auth`
  - Launch avatar GUI: `uv run python -m src.chatty_commander.main --gui`
  - Dev client will attempt to connect to ws://localhost:8100/avatar/ws

## CLI and REPL usage

Basic help:

Start interactive REPL:

Example session (stdin-driven):

This flow is covered by automated tests: see \[tests.test_repl_basic.test_repl_quick_session_executes_and_exits_cleanly():1\].

## Contributing

Contributions are welcome! For larger changes or new features, please start by opening an RFC issue using the provided template and follow the [RFC process](docs/RFC_PROCESS.md).
