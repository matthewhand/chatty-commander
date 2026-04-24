# ChattyCommander

An advanced AI-powered voice command system with a modern Web interface, capable of executing complex workflows, system interactions, and real-time communication.

![Dashboard Preview](docs/images/dashboard.png)

## Getting Started
We have recently restructured our documentation to make onboarding easier!

Please refer to the organized **User Guide** below:

1. [Installation Guide](docs/user-guide/01_INSTALLATION.md)
2. [Configuration Guide](docs/user-guide/02_CONFIGURATION.md)
3. [Dashboard & Web UI](docs/user-guide/03_DASHBOARD_AND_WEBUI.md)
4. [Voice Modes & Commands](docs/user-guide/04_VOICE_MODES_AND_COMMANDS.md)



## Usage

### CLI Mode

```bash
# Run with default settings
chatty-commander

# Run in web mode
chatty-commander web --port 8080

# Run with specific config
chatty-commander --config my_config.json
```

### Python API

```python
from chatty_commander.app.orchestrator import main_loop

# Start the voice assistant
main_loop()
```

## Developer Documentation
Looking to modify the core functionality or add new LLM adapters?
Check out our extensive [Developer Docs](docs/developer/) section.

## License
MIT License


## Installation

```bash
pip install chatty-commander
```


## Configuration

Edit `config.json` to customize commands and settings.


## Quick Start

```bash
# Start with default configuration
chatty-commander

# Start with custom config
chatty-commander --config /path/to/config.json

# Start in web mode
chatty-commander --mode web

# Enable voice control
chatty-commander --voice --wakeword hey_computer
```


## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/version` | GET | Get application version |
| `/health` | GET | Health check |
| `/agents` | GET | List available agents |
| `/agents` | POST | Create new agent |
| `/config` | GET | Get configuration |
| `/config` | POST | Update configuration |
| `/commands` | GET | List commands |
| `/commands` | POST | Execute command |
| `/ws` | WS | WebSocket for real-time updates |

### WebSocket Events

- `agent_state_change` - Agent status updates
- `command_executed` - Command execution results
- `voice_detected` - Wake word detection events


## Development

### Setup
```bash
git clone https://github.com/matthewhand/chatty-commander.git
cd chatty-commander
pip install -e ".[dev]"
```

### Running Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Smoke tests
pytest tests/smoke/ -v

# E2E tests
pytest tests/e2e/ -v

# With coverage
pytest --cov=src/chatty_commander --cov-report=html
```

### Code Quality
```bash
# Run linting
flake8 src/
mypy src/

# Run QA agents
python -m qa.fleet_commander
```


## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Checklist
- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black src/`)
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] README updated if needed
