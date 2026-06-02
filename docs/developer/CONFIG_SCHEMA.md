# Configuration Schema

ChattyCommander uses a JSON-based configuration file (`config.json`) with sensible defaults.

## Top-Level Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `commands` | object | `{}` | Voice command mappings |
| `states` | object | `{}` | State/mode definitions |
| `advisors` | object | `{}` | LLM advisor configuration |
| `audio` | object | `{}` | Audio capture settings |
| `web` | object | `{}` | Web server settings |

## `commands` Schema

```json
{
  "commands": {
    "<command_name>": {
      "type": "keypress|url|system",
      "action": "<action_string>"
    }
  }
}
```

**Types:**
- `keypress` — keyboard shortcut (e.g. `"ctrl+shift+;"`)
- `url` — HTTP request to a URL (e.g. Home Assistant)
- `system` — shell command

## `advisors` Schema

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
    "bridge": { "token": "secret" },
    "platforms": ["discord", "slack"],
    "personas": {
      "default": "philosophy_advisor"
    },
    "memory": {
      "persistence_enabled": false,
      "persistence_path": "data/advisors_memory.jsonl"
    }
  }
}
```

## `audio` Schema

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 1280,
    "device_index": null
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `LLM_BACKEND` | Preferred LLM backend (`openai`, `ollama`, `local`, `mock`) |
| `PORT` | Server port (default `8100`) |
| `NO_AUTH` | Set to `1` to disable authentication |
| `CHATCOMM_LOG_LEVEL` | Logger level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) applied in web mode. The `--log-level` CLI flag takes precedence. |

See `.env.example` for a template.

## Config File Writes

`config.json` is written **atomically** (written to a temp file, then `os.replace`d into place), so a crash mid-write cannot leave a corrupt or partially-written config on disk.

> **Note:** `set_start_on_boot` persists the preference but does not yet implement OS-level autostart; it logs that the platform integration is not implemented.
