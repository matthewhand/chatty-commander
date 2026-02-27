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

## Managing Commands via WebUI
You can view the currently configured commands in the WebUI. The Commands page dynamically loads the command definitions from the backend configuration.

![Commands Page](../screenshots/commands.png)

This list reflects the `commands` section of your `config.json` file. Each card displays:
*   **Command Name**: The identifier of the command.
*   **Action Type**: The type of action (e.g., `keypress`, `url`, `shell`).
*   **Payload**: The specific details of the action (e.g., the key combination, URL, or shell command).
*   **Activation Triggers**: While currently read-only in the UI, this section indicates how the command can be triggered (e.g., via REST API).
