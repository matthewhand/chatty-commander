# Avatar GUI

The Avatar GUI is an optional 3D anime-style avatar that provides visual feedback for ChattyCommander's states.

## Starting the Avatar

```bash
# Start backend first
uv run python main.py --web --no-auth --port 8100

# Then start the avatar GUI
uv run python -m chatty_commander.cli.cli gui
```

Or combined:
```bash
uv run python main.py --gui
```

## WebSocket Protocol

The avatar connects to `ws://localhost:8100/avatar/ws` and receives JSON messages:

### State Messages

```json
{
  "type": "state_change",
  "data": {
    "agent_id": "discord-channel-user",
    "state": "thinking",
    "message": "Processing your message..."
  }
}
```

**States:**
| State | Description |
|-------|-------------|
| `idle` | Default, waiting for input |
| `thinking` | Processing user input |
| `processing` | Generating LLM response |
| `tool_call` | Executing a tool (e.g. browser analyst) |
| `responding` | Delivering response |
| `error` | Error occurred |

### Avatar Animation Control

```json
{
  "type": "animation",
  "data": {
    "action": "talk",
    "duration_ms": 2000
  }
}
```

## Settings API

The avatar settings page communicates with:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/config` | GET | Fetch current settings |
| `/api/v1/config` | PUT | Save settings |
| `/api/v1/version` | GET | Display version info |

## Discovery

The avatar client does a health check at `http://localhost:8100/health` on startup. If unavailable, it retries with exponential backoff.

## Development Tips

- Run the backend with `--debug` flag for verbose state logs
- Use browser DevTools WebSocket inspector to monitor messages
- Avatar state changes are broadcast to **all** connected WebSocket clients
