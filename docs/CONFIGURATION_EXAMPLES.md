# ChattyCommander Configuration Examples

This guide showcases different configuration profiles for various use cases, from minimal voice-only setups to full AI assistant configurations.

## 🎤 Voice-Only Configuration

Perfect for controlling external applications like codex-cli with pure voice commands.

**Use Case**: Voice-controlled coding assistant that integrates with existing tools without any UI overhead.

### Features
- No web UI or GUI popups
- Keybinding-based transcription control
- Minimal resource usage
- Perfect for IDE integration

### Setup
```bash
cp configs/voice-only-example.json config.json
chatty-commander run --voice-only
```

### Workflow Example: Voice-Controlled Codex-CLI

**🎬 VIDEO PLACEHOLDER: Voice-Controlled Codex-CLI Demo**
> *[Insert video here showing the complete workflow: wake word → voice command → codex-cli interaction → code generation]*

The voice-only configuration enables this powerful workflow:

1. **Say wake word**: "Hey coder" or press `Ctrl+Shift+V`
2. **Speak your request**: "Create a Python function that validates email addresses"
3. **Automatic processing**: 
   - Voice transcribed locally using Whisper
   - Text automatically pasted and sent to codex-cli
   - Generated code appears in your editor
4. **Seamless integration**: No UI interruptions, pure voice-to-code workflow

#### Key Bindings (Customizable)
- `Ctrl+Shift+V`: Start voice transcription
- `Ctrl+Shift+Enter`: End transcription, paste, and execute
- `Ctrl+Alt+C`: Trigger codex-cli with voice input

#### Benefits
- **Hands-free coding**: Keep hands on keyboard while describing code
- **Natural language**: Describe what you want in plain English
- **IDE agnostic**: Works with any text editor or terminal
- **Offline capable**: Local Whisper transcription, no internet required

---

## 🤖 Full AI Assistant Configuration

Complete smart home and productivity assistant with web UI and avatar.

**Use Case**: Comprehensive voice assistant for home automation, productivity, and entertainment.

### Features
- Voice control with wake words
- Web dashboard at http://localhost:8100
- Avatar animations and visual feedback
- Home Assistant integration
- OpenAI GPT integration for natural language

### Setup
```bash
cp configs/full-assistant-example.json config.json
# Configure your API keys and Home Assistant details
chatty-commander run --web --avatar
```

### Available Commands
- **Smart Home**: "Turn on the lights", "Set temperature to 72"
- **Weather**: "What's the weather like?"
- **Entertainment**: "Play some music", "Turn on the TV"
- **Productivity**: "What time is it?", "Set a reminder"

---

## 💻 Developer Tools Configuration

Voice-controlled development workflow with git, testing, and IDE integration.

**Use Case**: Streamline development tasks with voice commands for git, testing, and code formatting.

### Features
- Git command integration
- Test execution with voice
- Code formatting automation
- IDE keybinding triggers
- Terminal command execution

### Setup
```bash
cp configs/developer-tools-example.json config.json
chatty-commander run --dev-mode
```

### Workflow Examples

#### Git Workflow
1. "Hey dev, check git status"
2. "Add all changes"
3. "Create commit" (opens IDE commit dialog)

#### Testing & Quality
1. "Hey dev, format code"
2. "Run tests"
3. "Check test results"

---

## Configuration Comparison

| Feature | Voice-Only | Full Assistant | Developer Tools |
|---------|------------|----------------|-----------------|
| Voice Control | ✅ | ✅ | ✅ |
| Web UI | ❌ | ✅ | ✅ |
| Avatar | ❌ | ✅ | ❌ |
| Smart Home | ❌ | ✅ | ❌ |
| IDE Integration | ✅ | ❌ | ✅ |
| Git Commands | ❌ | ❌ | ✅ |
| Resource Usage | Minimal | High | Medium |
| Best For | External Tools | Home Assistant | Development |

## Creating Custom Configurations

### Basic Structure
```json
{
  "profile_name": "My Custom Profile",
  "description": "Description of this configuration",
  "default_state": "idle",
  "model_actions": {
    "command_name": {
      "action_type": { "config": "value" }
    }
  },
  "voice": {
    "enabled": true,
    "wake_words": ["custom_wake_word"],
    "transcription_backend": "whisper_local"
  },
  "ui": {
    "web_enabled": false,
    "gui_enabled": false,
    "avatar_enabled": false
  }
}
```

### Action Types

#### Keypress Actions
```json
"action_name": {
  "keypress": {
    "keys": "ctrl+shift+v",
    "description": "Description of what this does"
  }
}
```

#### Shell Commands
```json
"action_name": {
  "shell": {
    "cmd": "echo 'Hello World'",
    "capture_output": true,
    "confirm": false
  }
}
```

#### HTTP Requests
```json
"action_name": {
  "url": {
    "url": "https://api.example.com/endpoint",
    "method": "POST",
    "headers": {"Authorization": "Bearer TOKEN"},
    "data": {"key": "value"}
  }
}
```

#### Messages/Notifications
```json
"action_name": {
  "message": {
    "text": "This is a notification message"
  }
}
```

## Tips for Configuration

### Voice-Only Optimization
- Use simple, distinct wake words
- Configure appropriate silence timeouts
- Test keybindings don't conflict with your apps
- Use local Whisper for privacy and offline operation

### Performance Tuning
- Disable unused features (web UI, avatar, etc.)
- Adjust transcription timeouts based on your speaking pace
- Use shorter wake words for faster activation
- Configure silence detection threshold for your environment

### Integration Best Practices
- Map voice commands to existing hotkeys when possible
- Use descriptive command names that are easy to remember
- Group related commands with similar prefixes
- Test commands individually before creating complex workflows

## Testing Your Configuration

```bash
# Test voice commands
chatty-commander voice test --config your-config.json --mock --duration 10

# Validate configuration
chatty-commander config --validate --file your-config.json

# List available commands
chatty-commander list --config your-config.json

# Test specific command
chatty-commander exec command_name --dry-run --config your-config.json
```

## Troubleshooting

### Voice Recognition Issues
- Check microphone permissions
- Adjust silence timeout settings
- Test with mock transcription first
- Verify wake word pronunciation

### Keybinding Conflicts
- Test bindings don't conflict with system shortcuts
- Use unique modifier combinations
- Check application-specific hotkeys

### Performance Issues
- Disable unused UI components
- Use local transcription instead of API calls
- Reduce wake word sensitivity if getting false positives

---

## Next Steps

1. **Choose a configuration** that matches your use case
2. **Customize the commands** to fit your specific workflow
3. **Test incrementally** - start with basic commands and expand
4. **Create workflows** by chaining multiple commands together
5. **Share your config** - contribute back useful configurations to the community!

For more advanced configuration options, see the [API Documentation](API.md) and [Architecture Overview](ARCHITECTURE_OVERVIEW.md).