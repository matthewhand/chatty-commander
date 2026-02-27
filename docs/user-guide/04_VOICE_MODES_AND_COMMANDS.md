# Voice Modes & Commands

ChattyCommander supports multiple voice interfaces for natural language execution.

## The Wake Word engine
The project currently uses `OpenWakeWord` for robust edge-based active listening.
You can configure the exact model and threshold passing in `config.json`.

## Available States
1. **Idle**: Waiting for the wake word (e.g. "Computer" or "Hey Chatty").
2. **Computer**: Processing a single request and returning to idle.
3. **Chatty**: Keeping the microphone open for sequential commands.

## Custom Voice Commands
You can map specific voice triggers to CLI commands or internal Python functions by modifying the JSON profiles within the backend configs.

The **Commands** page in the WebUI displays your current active configuration. It lists all available commands, their types (e.g., `keypress`, `shell`), and their execution payloads. This view is read-only and reflects the `commands` section of your `config.json`.

To verify your commands are loaded correctly:
1. Navigate to the WebUI (default `http://localhost:8100`).
2. Click on the "Commands" tab.
3. Review the list of commands. Each card shows the command key and its configured action details.
