
# Documentation

This directory contains comprehensive documentation for the ChattyCommander project.

## Available Documentation

- **[Architecture Overview](ARCHITECTURE_OVERVIEW.md)** - High-level system architecture and component relationships
- **[Modes of Operation](MODES_OF_OPERATION.md)** - Detailed explanation of CLI, Web, GUI, and Shell modes
- **[OpenAI Agents Advisor](OPENAI_AGENTS_ADVISOR.md)** - Design and implementation of the AI advisor system
- **[Recurring Prompts](RECURRING_PROMPTS.md)** - Blueprint for scheduled, self-contained prompts

## Quick Reference

### Core Modes
- **CLI Mode**: `python main.py` - Voice-activated commands
- **Web Mode**: `python main.py --web` - FastAPI backend + React frontend
- **GUI Mode**: `python main.py --gui` - Desktop UI for configuration
- **Shell Mode**: `python main.py --shell` - Interactive text input

### Optional Features
- **Advisors**: `python main.py --advisors` - AI-powered assistant
- **Discord Bridge**: `python main.py --enable-discord-bridge` - External messaging
- **OpenWakeWord**: `python main.py --enable-openwakeword` - Voice wake word
- **Computer Vision**: `python main.py --enable-computer-vision` - Visual commands

### Orchestrator Mode
Combine multiple modes and features:
```bash
python main.py --orchestrate --enable-text --enable-web --advisors
```

## OS-specific launchers

- **Windows**: `./scripts/windows/start-web.ps1`
- **macOS**: `./scripts/macos/start-web.sh`

## Development

### Testing
```bash
# Run all tests
uv run pytest -q

# Test specific components
uv run pytest -q tests/test_web_mode.py
uv run pytest -q tests/test_advisors_service.py
```

### API Testing
```bash
# Start web server
python main.py --web --no-auth

# Test advisor API
curl -X POST http://localhost:8100/api/v1/advisors/message \
  -H "Content-Type: application/json" \
  -d '{"platform":"web","channel":"test","user":"user123","text":"Hello"}'
```
