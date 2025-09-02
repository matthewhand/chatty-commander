# ChattyCommander API Documentation

_Generated on 2025-08-21 09:00:07_

## Overview

ChattyCommander provides a RESTful API and WebSocket interface for voice command automation. The API allows you to:

- Monitor system status and health
- Manage configuration settings
- Control operational states
- Execute voice commands programmatically
- Receive real-time updates via WebSocket

## Base URL

```
http://localhost:8100
```

## Authentication

The API supports optional authentication. When running in development mode with `--no-auth`, no authentication is required.

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

Retrieves the current system configuration.

**Response Example:**

```json
{
  "general_models_path": "./models-idle",
  "system_models_path": "./models-computer",
  "chat_models_path": "./models-chatty",
  "model_actions": {
    "lights_on": {
      "url": "http://192.168.1.100/api/lights/on"
    },
    "screenshot": {
      "keypress": "cmd+shift+4"
    }
  },
  "default_state": "idle"
}
```

#### PUT /api/v1/config

Updates the system configuration. Some changes may require a restart.

**Request Body:** Same structure as GET response

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

#### System Event

```json
{
  "type": "system_event",
  "data": {
    "event": "model_loaded",
    "details": "Loaded 5 models for computer state",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (endpoint or resource not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

Error responses include a JSON body with details:

```json
{
  "error": "Invalid command",
  "details": "Command 'invalid_command' not found in configuration",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

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
fetch("http://localhost:8100/api/v1/status")
  .then((response) => response.json())
  .then((data) => console.log("Status:", data));

// Execute command
fetch("http://localhost:8100/api/v1/command", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ command: "lights_on" }),
})
  .then((response) => response.json())
  .then((data) => console.log("Command result:", data));

// WebSocket connection
const ws = new WebSocket("ws://localhost:8100/ws");
ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("WebSocket message:", data);
};
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running with `python main.py --web`
1. **CORS Errors**: Use `--no-auth` flag for development
1. **WebSocket Connection Failed**: Check firewall settings and ensure port 8100 is accessible
1. **Command Not Found**: Verify the command exists in your configuration

### Debug Mode

Run the server with debug logging:

```bash
python main.py --web --log-level DEBUG
```

### Health Check

#### GET /api/v1/health

Simple health check endpoint.

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": "2h 15m 30s"
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

#### System Event

```json
{
  "type": "system_event",
  "data": {
    "event": "model_loaded",
    "details": "Loaded 5 models for computer state",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (endpoint or resource not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

Error responses include a JSON body with details:

```json
{
  "error": "Invalid command",
  "details": "Command 'invalid_command' not found in configuration",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

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
fetch("http://localhost:8100/api/v1/status")
  .then((response) => response.json())
  .then((data) => console.log("Status:", data));

// Execute command
fetch("http://localhost:8100/api/v1/command", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ command: "lights_on" }),
})
  .then((response) => response.json())
  .then((data) => console.log("Command result:", data));

// WebSocket connection
const ws = new WebSocket("ws://localhost:8100/ws");
ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("WebSocket message:", data);
};
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running with `python main.py --web`
1. **CORS Errors**: Use `--no-auth` flag for development
1. **WebSocket Connection Failed**: Check firewall settings and ensure port 8100 is accessible
1. **Command Not Found**: Verify the command exists in your configuration

### Debug Mode

Run the server with debug logging:

```bash
python main.py --web --log-level DEBUG
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
