# ChattyCommander API Documentation

## Overview

ChattyCommander provides a RESTful API and WebSocket interface for voice command automation. The API allows you to:

- Monitor system status and health
- Manage configuration settings
- Control operational states
- Execute voice commands programmatically
- Authenticate and manage tokens
- Receive real-time updates via WebSocket

> This file is maintained by hand to match the running server. A machine-readable
> spec is also generated to `docs/openapi.json`; when the server is running you
> can browse the interactive docs at `/docs` (Swagger UI) and `/redoc`.

## Base URL

```
http://localhost:8100
```

## Authentication

The API supports optional authentication. When running in development mode with
`--no-auth`, no authentication is required (dev only — structurally refused in
production). With auth enabled, obtain a token via `POST /api/v1/auth/login` and
send it as `Authorization: Bearer <access_token>`. Service-to-service callers may
instead present a scoped key via the `X-API-Key` header.

### POST /api/v1/auth/login

Exchange credentials for an access + refresh token pair. Returns `404` when user
auth is not configured (the frontend then falls back to its no-auth probe).

**Request Body:**
```json
{
  "username": "admin",
  "password": "your-password"
}
```

**Response Example:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "<jwt>"
}
```

### POST /api/v1/auth/refresh

Rotate tokens: the presented `refresh_token` is consumed (its `jti` is revoked)
and a **new** access + refresh token pair is issued, so a leaked-then-rotated
refresh token is single-use.

**Request Body:**
```json
{
  "refresh_token": "<jwt>"
}
```

**Response Body:** Same shape as the login response (a fresh token pair).

### POST /api/v1/auth/logout

Revoke the presented Bearer access token's `jti` (and the refresh token's `jti`
if one is supplied in the body) via the denylist.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body (optional):**
```json
{
  "refresh_token": "<jwt>"
}
```

### GET /api/v1/auth/me

Return the authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Response Example:**
```json
{
  "username": "admin",
  "is_active": true,
  "roles": ["admin"]
}
```

## API Endpoints

### System Status

#### GET /api/v1/status

Returns the current system status including active state and loaded models.

**Response Example:**
```json
{
  "status": "running",
  "current_state": "idle",
  "active_models": ["hey_chat_tee", "hey_khum_puter"],
  "uptime": "2h 15m 30s",
  "version": "0.2.0"
}
```

### Configuration Management

#### GET /api/v1/config

Retrieves the current system configuration. The shape mirrors `config.json`
(loaded by `src/chatty_commander/app/config.py`). Top-level keys include
`model_paths`, `commands`, `state_models`, `default_state`, `general`,
`web_server`, and the optional `advisors`/`voice`/`ui` blocks.

**Response Example:**
```json
{
  "model_paths": {
    "idle": "models-idle",
    "computer": "models-computer",
    "chatty": "models-chatty"
  },
  "commands": {
    "take_screenshot": {
      "action": "keypress",
      "keys": "take_screenshot"
    },
    "lights_on": {
      "action": "url",
      "url": "{home_assistant}/lights_on"
    },
    "thanks_chat_tee": {
      "action": "custom_message",
      "message": "That'll do, bro"
    }
  },
  "state_models": {
    "idle": ["hey_chat_tee", "hey_khum_puter", "lights_on", "lights_off"],
    "computer": ["oh_kay_screenshot", "okay_stop"],
    "chatty": ["wax_poetic", "thanks_chat_tee"]
  },
  "default_state": "idle"
}
```

#### PUT /api/v1/config

Updates the system configuration. Some changes may require a restart.

**Request Body:** Same structure as the GET response.

### State Management

#### GET /api/v1/state

Returns the current operational state.

**Response Example:**
```json
{
  "current_state": "idle",
  "active_models": ["hey_chat_tee", "hey_khum_puter"],
  "last_command": "hey_chat_tee",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /api/v1/state

Manually changes the system state.

**Request Body:**
```json
{
  "state": "computer"
}
```

**Valid states:** `idle`, `computer`, `chatty`

### Command Execution

#### POST /api/v1/command

Executes a voice command programmatically.

**Request Body:**
```json
{
  "command": "lights_on",
  "parameters": {
    "brightness": 80
  }
}
```

**Response Example:**
```json
{
  "success": true,
  "message": "Command executed successfully",
  "execution_time": 150
}
```

## WebSocket Interface

### Connection

Connect to the WebSocket endpoint for real-time updates:

```
ws://localhost:8100/ws
```

### Message Types

The WebSocket sends JSON messages with the following types:

#### State Change
```json
{
  "type": "state_change",
  "data": {
    "old_state": "idle",
    "new_state": "computer",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Command Detection
```json
{
  "type": "command_detected",
  "data": {
    "command": "hey_chat_tee",
    "confidence": 0.95,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### dograh Status

When the dograh integration is configured, the server pushes a `dograh_status`
message after connect (and active calls broadcast `dograh_call_state`), so the
dashboard's status card updates live. This is computed from the same source as
`GET /api/v1/dograh/status`.

```json
{
  "type": "dograh_status",
  "data": {
    "available": true,
    "version": "1.2.3"
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid token)
- `404` - Not Found (endpoint or resource not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

Error responses use a standardized envelope (`web/errors.py`):

```json
{
  "error": "Invalid command",
  "code": "command_not_found",
  "details": "Command 'invalid_command' not found in configuration",
  "request_id": "..."
}
```

Endpoints degrade gracefully: a missing integration or hardware returns a `200`
with an honest empty state rather than a `500`.

## Rate Limiting

Basic in-memory per-IP rate limiting is implemented via `RateLimitMiddleware`
(default 60 req/min, `X-RateLimit-*` headers, secure client IP extraction
considering trusted proxies). See `src/chatty_commander/web/web_mode.py`.

- Not yet Redis-backed or per-endpoint configurable (roadmap item).
- Suitable for dev/single-instance; production should consider distributed limiting + nginx/ingress rules (see SECURITY.md).

## Examples

### Python Client Example

```python
import requests
import websockets
import asyncio
import json

# Basic API usage
response = requests.get('http://localhost:8100/api/v1/status')
status = response.json()
print(f"System status: {status['status']}")

# Execute a command
command_data = {"command": "lights_on"}
response = requests.post('http://localhost:8100/api/v1/command', json=command_data)
result = response.json()
print(f"Command result: {result['success']}")

# WebSocket client
async def websocket_client():
    uri = "ws://localhost:8100/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data['type']} - {data['data']}")

# Run WebSocket client
# asyncio.run(websocket_client())
```

### JavaScript/Browser Example

```javascript
// Fetch system status
fetch('http://localhost:8100/api/v1/status')
  .then(response => response.json())
  .then(data => console.log('Status:', data));

// Execute command
fetch('http://localhost:8100/api/v1/command', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({command: 'lights_on'})
})
.then(response => response.json())
.then(data => console.log('Command result:', data));

// WebSocket connection
const ws = new WebSocket('ws://localhost:8100/ws');
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('WebSocket message:', data);
};
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running with `chatty-commander --web`
2. **CORS Errors**: Use `--no-auth` flag for development
3. **WebSocket Connection Failed**: Check firewall settings and ensure port 8100 is accessible
4. **Command Not Found**: Verify the command exists in your configuration

### Debug Mode

Run the server with debug logging:

```bash
chatty-commander --web --log-level DEBUG
```

### Health Check

Use the status endpoint to verify the API is working:

```bash
curl http://localhost:8100/api/v1/status
```

## Changelog

### Version 0.2.0
- Added comprehensive API endpoints
- Implemented WebSocket support
- Added state management
- Enhanced error handling

### Version 0.1.0
- Initial API implementation
- Basic command execution
- Configuration management
