# Usage Guide

This guide demonstrates the main interaction points of Chatty Commander, showing how to configure personas, assign tools, set up 3D avatars, and configure TTS/STT functionality.

## Overview

Chatty Commander provides several key interaction areas:

- **Persona Management**: Configure AI advisor personalities and behaviors
- **Tool Assignment**: Assign specific tools and capabilities to personas
- **3D Avatar Integration**: Set up visual avatars with animations and themes
- **Voice Integration**: Configure Text-to-Speech (TTS) and Speech-to-Text (STT)

## Getting Started

### 1. Persona Configuration

Personas define the personality and behavior of your AI advisors. You can configure them through the configuration file or the planned web interface.

![Persona Configuration Interface](images/persona-setup-screenshot.png)
_Screenshot placeholder: Shows the persona configuration interface with fields for name, system prompt, and behavior settings_

**Current Implementation Status**: ✅ **Available**

- Basic persona system implemented in `src/chatty_commander/advisors/prompting.py`
- Default personas available: `philosophy_advisor`
- Configuration via `config.json` under `advisors.personas`

**Example Configuration**:

```json
{
  "advisors": {
    "personas": {
      "philosophy_advisor": "Answer concisely in the style of a Stoic philosopher. Cite relevant thinkers when helpful.",
      "technical_expert": "Provide detailed technical explanations with code examples when relevant.",
      "creative_writer": "Respond with creativity and flair, using vivid language and storytelling."
    }
  }
}
```

### 2. Tool Assignment to Personas

Each persona can be assigned specific tools and capabilities based on their role and the current mode.

![Tool Assignment Interface](images/tool-assignment-screenshot.png)
_Screenshot placeholder: Shows the tool assignment interface with drag-and-drop functionality for assigning tools to personas_

**Current Implementation Status**: ⚠️ **Partially Available**

- Tool assignment exists in mode configuration
- Available tools: `keypress`, `http`, `browser`, `avatar_talkinghead`, `tts`, `stt`
- UI for tool assignment is planned but not yet implemented

**Example Configuration**:

```json
{
  "modes": {
    "chatty": {
      "wakewords": [],
      "persona": "philosophy_advisor",
      "tools": ["avatar_talkinghead", "tts", "stt"]
    },
    "focus": {
      "wakewords": ["focus_on"],
      "persona": "technical_expert",
      "tools": ["browser", "keypress"]
    }
  }
}
```

### 3. 3D Avatar Setup

Chatty Commander supports 3D avatars through the TalkingHead integration, providing visual representation of your AI advisors.

![Avatar Configuration Interface](images/avatar-setup-screenshot.png)
_Screenshot placeholder: Shows the 3D avatar configuration interface with avatar selection, theme customization, and animation settings_

**Current Implementation Status**: ⚠️ **In Development**

- Avatar GUI framework implemented in `src/chatty_commander/webui/avatar/`
- WebSocket communication for state updates available
- Animation system and theme mapping planned
- Avatar-persona mapping partially implemented

**Key Features**:

- Transparent desktop window overlay
- Real-time state animations (thinking, processing, responding)
- Persona-based theme switching
- WebSocket-based state synchronization

### 4. Avatar Animation States

Avatars respond to different AI states with appropriate animations:

![Avatar Animation States](images/avatar-animations-screenshot.png)
_Screenshot placeholder: Shows different avatar animation states - idle, thinking, processing, tool_calling, responding, error_

**Animation States**:

- **Idle**: Neutral breathing/idle animation
- **Thinking**: Triggered when LLM emits `<thinking>` content
- **Processing**: General background processing animation
- **Tool Calling**: "Hacking" animation during tool/function calls
- **Responding**: Speaking/response animation
- **Error**: Error/glitch animation
- **Handoff**: Transition animation when switching between agents

### 5. TTS (Text-to-Speech) Configuration

Configure voice output for your AI advisors:

![TTS Configuration Interface](images/tts-setup-screenshot.png)
_Screenshot placeholder: Shows TTS configuration with voice selection, speed controls, and audio output settings_

**Current Implementation Status**: 📋 **Planned**

- TTS integration planned in roadmap
- Voice synthesis for avatar lip-sync planned
- Per-persona voice configuration planned

### 6. STT (Speech-to-Text) Configuration

Set up voice input for natural conversation with your AI advisors:

![STT Configuration Interface](images/stt-setup-screenshot.png)
_Screenshot placeholder: Shows STT configuration with microphone selection, wake word settings, and voice recognition options_

**Current Implementation Status**: 📋 **Planned**

- STT integration planned in roadmap
- Wake word detection system exists for mode switching
- Continuous voice conversation planned

### 7. Web Interface Overview

The web interface provides a centralized location for all configuration and monitoring:

![Web Interface Dashboard](images/web-interface-screenshot.png)
_Screenshot placeholder: Shows the main web interface with navigation, real-time status, and configuration panels_

**Current Implementation Status**: ✅ **Available**

- Web server implemented with FastAPI
- Avatar WebSocket endpoint available
- Settings interface planned for comprehensive configuration

## Video Demonstration

### Complete Workflow Demo

![Video: Complete Chatty Commander Setup](videos/chatty-commander-demo.mp4)
_Video placeholder: Demonstrates the complete workflow of setting up Chatty Commander including:_

- _Adding and configuring new personas_
- _Assigning tools to personas based on their roles_
- _Setting up 3D avatars and selecting themes_
- _Configuring TTS voice settings_
- _Setting up STT and wake word detection_
- _Testing the complete interaction flow_

**Video Contents** (Planned):

1. **Introduction** (0:00-0:30): Overview of Chatty Commander capabilities
1. **Persona Setup** (0:30-2:00): Creating and configuring AI advisor personas
1. **Tool Assignment** (2:00-3:30): Assigning specific tools and capabilities
1. **Avatar Configuration** (3:30-5:00): Setting up 3D avatars and themes
1. **Voice Setup** (5:00-6:30): Configuring TTS and STT settings
1. **Live Demonstration** (6:30-8:00): Real-time interaction with configured system
1. **Advanced Features** (8:00-9:00): Team orchestration and agent handoffs

## Implementation Status Summary

| Feature                 | Status         | Implementation Location                      |
| ----------------------- | -------------- | -------------------------------------------- |
| **Persona Management**  | ✅ Available   | `src/chatty_commander/advisors/prompting.py` |
| **Tool Assignment**     | ⚠️ Config Only | `config.json` modes section                  |
| **3D Avatar Framework** | ⚠️ In Progress | `src/chatty_commander/webui/avatar/`         |
| **Avatar Animations**   | 📋 Planned     | TODO: Animation state machine                |
| **TTS Integration**     | 📋 Planned     | TODO: Voice synthesis                        |
| **STT Integration**     | 📋 Planned     | TODO: Speech recognition                     |
| **Web UI Settings**     | 📋 Planned     | TODO: Comprehensive settings interface       |
| **Agent Blueprints**    | 📋 Planned     | TODO: Natural language agent creation        |

## Quick Start Commands

```bash
# Start the web interface
uv run python -m src.chatty_commander.main --web --no-auth

# Launch the avatar GUI
uv run python -m src.chatty_commander.main --gui

# View current configuration
chatty config --list

# Test persona configuration
chatty exec hello --dry-run
```

## Next Steps

Based on the current implementation status:

1. **Immediate**: Use existing persona and tool configuration via `config.json`
1. **Short-term**: Avatar GUI development and animation system
1. **Medium-term**: TTS/STT integration and voice interaction
1. **Long-term**: Complete web UI for all configuration and agent blueprint management

For detailed implementation plans, see:

- <mcfile name="TODO.md" path="docs/TODO.md"></mcfile> - Current development roadmap
- <mcfile name="CUSTOM_MODES_AND_PERSONAS.md" path="docs/CUSTOM_MODES_AND_PERSONAS.md"></mcfile> - Configuration guide
- <mcfile name="ARCHITECTURE.md" path="ARCHITECTURE.md"></mcfile> - System architecture overview
