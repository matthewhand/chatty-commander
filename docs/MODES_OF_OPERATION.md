# ChattyCommander Modes of Operation

## Overview

ChattyCommander operates in **4 main modes**, all unified by the `ModeOrchestrator` that shares core business logic while providing different input methods and user interfaces.

## Core Modes

### 1. CLI Mode (Default) - Voice-Activated Commands
**Purpose**: Traditional voice command interface with continuous listening
- **Input**: Voice commands via microphone
- **Processing**: Voice → Text → State transitions → Action execution
- **Output**: System actions (keypresses, URLs, system commands)
- **Usage**: `python main.py`

**Flow**:
```
Voice Input → ModelManager (speech-to-text) → StateManager (state transitions) → CommandExecutor (actions)
```

### 2. Web Mode - FastAPI Backend + React Frontend
**Purpose**: Modern web interface with real-time capabilities
- **Input**: HTTP requests, WebSocket messages
- **Processing**: REST API endpoints, real-time WebSocket communication
- **Output**: JSON responses, WebSocket updates, system actions
- **Usage**: `python main.py --web`

**Key Endpoints**:
- `/api/v1/status` - System status
- `/api/v1/config` - Configuration management
- `/api/v1/state` - State transitions
- `/api/v1/command` - Command execution
- `/api/v1/advisors/*` - AI advisor interactions
- `/bridge/event` - Discord/Slack bridge

### 3. GUI Mode - Desktop UI
**Purpose**: Native desktop interface for configuration and control
- **Input**: Mouse clicks, keyboard shortcuts
- **Processing**: Desktop UI events, system tray integration
- **Output**: Visual feedback, configuration dialogs
- **Usage**: `python main.py --gui`

### 4. Shell Mode - Interactive Text Input
**Purpose**: Text-based command simulation for testing and development
- **Input**: Text commands via terminal
- **Processing**: Direct text → Command execution
- **Output**: System actions, command feedback
- **Usage**: `python main.py --shell`

## Shared Architecture

### Core Components (All Modes Use These)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Config      │    │  StateManager   │    │  ModelManager   │
│                 │    │                 │    │                 │
│ • Model paths   │    │ • State machine │    │ • Load models   │
│ • Commands      │    │ • Transitions   │    │ • Speech-to-text│
│ • Settings      │    │ • Triggers      │    │ • Model swapping│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ CommandExecutor  │
                    │                 │
                    │ • Keypresses    │
                    │ • URL calls     │
                    │ • System cmds   │
                    └─────────────────┘
```

### Mode Orchestrator
The `ModeOrchestrator` unifies all modes by:
- **Selecting adapters** based on CLI flags
- **Starting/stopping** mode-specific components
- **Routing commands** to shared `CommandExecutor`
- **Managing optional features** (OpenWakeWord, CV, Discord bridge)

## Optional Features

### Voice Wake Word (`--enable-openwakeword`)
- **Purpose**: Continuous listening for wake word
- **Integration**: Works with CLI mode
- **Usage**: `python main.py --enable-openwakeword`

### Computer Vision (`--enable-computer-vision`)
- **Purpose**: Visual command recognition
- **Integration**: Works with any mode
- **Usage**: `python main.py --enable-computer-vision`

### Discord/Slack Bridge (`--enable-discord-bridge`)
- **Purpose**: External messaging platform integration
- **Integration**: Node.js bridge connects to Web API
- **Usage**: `python main.py --enable-discord-bridge`

### AI Advisors (`--advisors`)
- **Purpose**: AI-powered assistant interactions
- **Integration**: Web API endpoints, context-aware memory
- **Usage**: `python main.py --advisors`

## Mode Selection Examples

### Single Mode
```bash
python main.py                    # CLI mode (default)
python main.py --web              # Web mode
python main.py --gui              # GUI mode
python main.py --shell            # Shell mode
```

### Multiple Modes (Orchestrator)
```bash
python main.py --orchestrate --enable-text --enable-web
python main.py --orchestrate --enable-gui --enable-discord-bridge
python main.py --orchestrate --enable-text --enable-web --advisors
```

### With Optional Features
```bash
python main.py --web --advisors --enable-discord-bridge
python main.py --orchestrate --enable-text --enable-openwakeword
```

## Data Flow Architecture

### Standard Command Flow
```
Input (Voice/Web/GUI/Text) 
    ↓
Adapter (Mode-specific)
    ↓
StateManager (State transitions)
    ↓
CommandExecutor (System actions)
    ↓
Output (Keypresses, URLs, System commands)
```

### Advisor Flow
```
Input (Web/Bridge) 
    ↓
AdvisorsService (Context-aware)
    ↓
LLM Provider (AI processing)
    ↓
Tools (Browser analyst, etc.)
    ↓
Response (AI-generated reply)
```

## Configuration

### Shared Config Structure
```json
{
  "models": {
    "idle": "path/to/idle/model",
    "computer": "path/to/computer/model",
    "chatty": "path/to/chatty/model"
  },
  "commands": {
    "open_browser": "start chrome",
    "volume_up": "keypress:volume_up"
  },
  "advisors": {
    "enabled": true,
    "providers": {
      "llm_api_mode": "completion",
      "model": "gpt-oss20b"
    },
    "context": {
      "personas": {
        "general": {"system_prompt": "You are helpful."},
        "philosopher": {"system_prompt": "You are philosophical."}
      }
    }
  }
}
```

## Development Workflow

### Testing Different Modes
```bash
# Test CLI mode
python main.py

# Test Web mode with no auth
python main.py --web --no-auth

# Test multiple modes
python main.py --orchestrate --enable-text --enable-web

# Test with advisors
python main.py --web --advisors
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

## Key Benefits

1. **Unified Logic**: All modes share the same core business logic
2. **Flexible Input**: Multiple ways to interact (voice, web, GUI, text)
3. **Optional Features**: Enable only what you need
4. **Consistent State**: State management works across all modes
5. **Extensible**: Easy to add new modes or features
6. **Testable**: Each mode can be tested independently

## Next Steps

The architecture is designed to support:
- **Real LLM integration** (replacing echo responses)
- **Advanced voice processing** (OpenWakeWord integration)
- **Computer vision commands** (visual recognition)
- **Multi-platform messaging** (Discord/Slack/Telegram)
- **Advanced AI features** (context switching, tool calling)
- **Production deployment** (Docker, Kubernetes, cloud hosting)
