# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from datetime import datetime
from typing import Any


def build_openapi_schema() -> dict[str, Any]:
    """
    Construct the OpenAPI schema dictionary.

    Note: This extracts the schema content from the previous APIDocumentationGenerator.generate_openapi_spec.
    It intentionally remains pure (no I/O, no logging) for ease of testing.
    """
    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": "ChattyCommander API",
            "description": "Voice command automation system with web interface",
            "version": "0.2.0",
            "contact": {
                "name": "ChattyCommander",
                "url": "https://github.com/your-repo/chatty-commander",
            },
            "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        },
        "servers": [
            {"url": "http://localhost:8100", "description": "Local development server"}
        ],
        "paths": {
            "/api/v1/status": {
                "get": {
                    "summary": "Get system status",
                    "description": "Returns the current status of the ChattyCommander system including active state and loaded models.",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "System status retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SystemStatus"
                                    },
                                    "example": {
                                        "status": "running",
                                        "current_state": "idle",
                                        "active_models": [
                                            "hey_chat_tee",
                                            "hey_khum_puter",
                                        ],
                                        "uptime": "2h 15m 30s",
                                        "version": "0.2.0",
                                    },
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/config": {
                "get": {
                    "summary": "Get configuration",
                    "description": "Returns the current system configuration including model paths and command mappings.",
                    "tags": ["Configuration"],
                    "responses": {
                        "200": {
                            "description": "Configuration retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Configuration"
                                    }
                                }
                            },
                        }
                    },
                },
                "put": {
                    "summary": "Update configuration",
                    "description": "Updates the system configuration. Requires restart for some changes to take effect.",
                    "tags": ["Configuration"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Configuration"}
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Configuration updated successfully"},
                        "400": {"description": "Invalid configuration data"},
                    },
                },
            },
            "/api/v1/state": {
                "get": {
                    "summary": "Get current state",
                    "description": "Returns the current operational state of the system (idle, computer, chatty).",
                    "tags": ["State Management"],
                    "responses": {
                        "200": {
                            "description": "Current state retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/StateInfo"
                                    },
                                    "example": {
                                        "current_state": "idle",
                                        "active_models": [
                                            "hey_chat_tee",
                                            "hey_khum_puter",
                                        ],
                                        "last_command": "hey_chat_tee",
                                        "timestamp": "2024-01-15T10:30:00Z",
                                    },
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Change state",
                    "description": "Manually change the system state to idle, computer, or chatty mode.",
                    "tags": ["State Management"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "state": {
                                            "type": "string",
                                            "enum": ["idle", "computer", "chatty"],
                                            "description": "Target state to transition to",
                                        }
                                    },
                                    "required": ["state"],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "State changed successfully"},
                        "400": {"description": "Invalid state specified"},
                    },
                },
            },
            "/api/v1/command": {
                "post": {
                    "summary": "Execute command",
                    "description": "Executes a voice command programmatically. Useful for testing and automation.",
                    "tags": ["Commands"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "command": {
                                            "type": "string",
                                            "description": "Command name to execute",
                                            "example": "lights_on",
                                        },
                                        "parameters": {
                                            "type": "object",
                                            "description": "Optional command parameters",
                                            "additionalProperties": True,
                                        },
                                    },
                                    "required": ["command"],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Command executed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "execution_time": {
                                                "type": "number",
                                                "description": "Execution time in milliseconds",
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        "400": {"description": "Invalid command or parameters"},
                        "404": {"description": "Command not found"},
                    },
                }
            },
            "/api/v1/health": {
                "get": {
                    "summary": "Health check",
                    "description": "Simple health check endpoint to verify server is running.",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "timestamp": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
                                            "uptime": {"type": "string"},
                                        },
                                    },
                                    "example": {
                                        "status": "healthy",
                                        "timestamp": "2024-01-15T10:30:00Z",
                                        "uptime": "2h 15m 30s",
                                    },
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/version": {
                "get": {
                    "summary": "Get version info",
                    "description": "Returns application semantic version and optional git SHA.",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Version info",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "version": {"type": "string"},
                                            "git_sha": {
                                                "type": ["string", "null"],
                                                "description": "Short git SHA if available",
                                            },
                                        },
                                        "required": ["version"],
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/ws": {
                "get": {
                    "summary": "WebSocket connection",
                    "description": "Establishes a WebSocket connection for real-time updates including state changes, command detections, and system events.",
                    "tags": ["WebSocket"],
                    "responses": {
                        "101": {"description": "WebSocket connection established"}
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "SystemStatus": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["running", "stopped", "error"],
                            "description": "Overall system status",
                        },
                        "current_state": {
                            "type": "string",
                            "enum": ["idle", "computer", "chatty"],
                            "description": "Current operational state",
                        },
                        "active_models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of currently loaded voice models",
                        },
                        "uptime": {
                            "type": "string",
                            "description": "System uptime in human-readable format",
                        },
                        "version": {
                            "type": "string",
                            "description": "Application version",
                        },
                    },
                    "required": ["status", "current_state", "active_models"],
                },
                "Configuration": {
                    "type": "object",
                    "properties": {
                        "general_models_path": {
                            "type": "string",
                            "description": "Path to general voice models",
                        },
                        "system_models_path": {
                            "type": "string",
                            "description": "Path to system command models",
                        },
                        "chat_models_path": {
                            "type": "string",
                            "description": "Path to chat interaction models",
                        },
                        "model_actions": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "keypress": {
                                        "type": "string",
                                        "description": "Keyboard shortcut to execute",
                                    },
                                    "url": {
                                        "type": "string",
                                        "description": "URL to request",
                                    },
                                },
                            },
                            "description": "Mapping of voice commands to actions",
                        },
                        "default_state": {
                            "type": "string",
                            "enum": ["idle", "computer", "chatty"],
                            "description": "Default state on startup",
                        },
                    },
                },
                "StateInfo": {
                    "type": "object",
                    "properties": {
                        "current_state": {
                            "type": "string",
                            "enum": ["idle", "computer", "chatty"],
                        },
                        "active_models": {"type": "array", "items": {"type": "string"}},
                        "last_command": {
                            "type": "string",
                            "description": "Last detected voice command",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Timestamp of last state change",
                        },
                    },
                    "required": ["current_state", "active_models"],
                },
            }
        },
        "tags": [
            {"name": "System", "description": "System status and health monitoring"},
            {"name": "Configuration", "description": "System configuration management"},
            {"name": "State Management", "description": "Operational state control"},
            {"name": "Commands", "description": "Voice command execution"},
            {"name": "WebSocket", "description": "Real-time communication"},
        ],
    }
    return spec


def generate_markdown_docs() -> str:
    """
    Return the long-form Markdown documentation string.

    This was previously generated dynamically with a timestamp embedded.
    To preserve that behavior while remaining pure, we only embed the timestamp at call time here.
    """
    docs = f"""
# ChattyCommander API Documentation

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

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
{{
  "status": "running",
  "current_state": "idle",
  "active_models": ["hey_chat_tee", "hey_khum_puter"],
  "uptime": "2h 15m 30s",
  "version": "0.2.0"
}}
```

### Configuration Management

#### GET /api/v1/config

Retrieves the current system configuration.

**Response Example:**
```json
{{
  "general_models_path": "./models-idle",
  "system_models_path": "./models-computer",
  "chat_models_path": "./models-chatty",
  "model_actions": {{
    "lights_on": {{
      "url": "http://192.168.1.100/api/lights/on"
    }},
    "screenshot": {{
      "keypress": "cmd+shift+4"
    }}
  }},
  "default_state": "idle"
}}
```

#### PUT /api/v1/config

Updates the system configuration. Some changes may require a restart.

**Request Body:** Same structure as GET response

### State Management

#### GET /api/v1/state

Returns the current operational state.

**Response Example:**
```json
{{
  "current_state": "idle",
  "active_models": ["hey_chat_tee", "hey_khum_puter"],
  "last_command": "hey_chat_tee",
  "timestamp": "2024-01-15T10:30:00Z"
}}
```

#### POST /api/v1/state

Manually changes the system state.

**Request Body:**
```json
{{
  "state": "computer"
}}
```

**Valid states:** `idle`, `computer`, `chatty`

### Command Execution

#### POST /api/v1/command

Executes a voice command programmatically.

**Request Body:**
```json
{{
  "command": "lights_on",
  "parameters": {{
    "brightness": 80
  }}
}}
```

**Response Example:**
```json
{{
  "success": true,
  "message": "Command executed successfully",
  "execution_time": 150
}}
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
{{
  "type": "state_change",
  "data": {{
    "old_state": "idle",
    "new_state": "computer",
    "timestamp": "2024-01-15T10:30:00Z"
  }}
}}
```

#### Command Detection
```json
{{
  "type": "command_detected",
  "data": {{
    "command": "hey_chat_tee",
    "confidence": 0.95,
    "timestamp": "2024-01-15T10:30:00Z"
  }}
}}
```

#### System Event
```json
{{
  "type": "system_event",
  "data": {{
    "event": "model_loaded",
    "details": "Loaded 5 models for computer state",
    "timestamp": "2024-01-15T10:30:00Z"
  }}
}}
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
{{
  "error": "Invalid command",
  "details": "Command 'invalid_command' not found in configuration",
  "timestamp": "2024-01-15T10:30:00Z"
}}
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
print(f"System status: {{status['status']}}")

# Execute a command
command_data = {{"command": "lights_on"}}
response = requests.post('http://localhost:8100/api/v1/command', json=command_data)
result = response.json()
print(f"Command result: {{result['success']}}")

# WebSocket client
async def websocket_client():
    uri = "ws://localhost:8100/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {{data['type']}} - {{data['data']}}")

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
fetch('http://localhost:8100/api/v1/command', {{
  method: 'POST',
  headers: {{
    'Content-Type': 'application/json',
  }},
  body: JSON.stringify({{command: 'lights_on'}})
}})
.then(response => response.json())
.then(data => console.log('Command result:', data));

// WebSocket connection
const ws = new WebSocket('ws://localhost:8100/ws');
ws.onmessage = function(event) {{
  const data = JSON.parse(event.data);
  console.log('WebSocket message:', data);
}};
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running with `python main.py --web`
2. **CORS Errors**: Use `--no-auth` flag for development
3. **WebSocket Connection Failed**: Check firewall settings and ensure port 8100 is accessible
4. **Command Not Found**: Verify the command exists in your configuration

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
"""
    return docs
