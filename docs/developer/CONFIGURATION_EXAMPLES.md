# Configuration Examples

Ready-to-use configuration profiles for different use cases.

## 🎤 Voice-Only Mode

Minimal setup for controlling external apps with pure voice commands:

```json
{
  "commands": {
    "okay_stop": {
      "type": "keypress",
      "action": "ctrl+shift+;"
    },
    "new_line": {
      "type": "keypress",
      "action": "enter"
    },
    "open_terminal": {
      "type": "keypress",
      "action": "ctrl+alt+t"
    }
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1
  }
}
```

Start with: `uv run python -m chatty_commander.cli.cli run`

## 🤖 Full AI Assistant

Complete smart home and productivity assistant with web UI and LLM:

```json
{
  "advisors": {
    "enabled": true,
    "llm_api_mode": "completion",
    "model": "gpt-4",
    "provider": {
      "base_url": "http://localhost:11434",
      "api_key": ""
    },
    "platforms": ["discord"],
    "personas": {
      "default": "philosophy_advisor"
    },
    "features": {
      "browser_analyst": true
    }
  },
  "commands": {
    "lights_on": {
      "type": "url",
      "action": "http://homeassistant.local:8123/api/services/light/turn_on"
    }
  }
}
```

Start with: `uv run python main.py --web --port 8100`

## 💻 Developer Tools

Voice-controlled git and IDE integration:

```json
{
  "commands": {
    "git_status": {
      "type": "system",
      "action": "git status"
    },
    "run_tests": {
      "type": "system",
      "action": "uv run pytest -q"
    },
    "format_code": {
      "type": "system",
      "action": "uv run ruff format ."
    },
    "save_file": {
      "type": "keypress",
      "action": "ctrl+s"
    }
  }
}
```

## Ollama Local LLM

For fully offline operation:

```json
{
  "advisors": {
    "enabled": true,
    "llm_api_mode": "completion",
    "model": "llama3.2",
    "provider": {
      "base_url": "http://localhost:11434/v1",
      "api_key": "ollama"
    }
  }
}
```

Requires Ollama running: `ollama serve` and `ollama pull llama3.2`
