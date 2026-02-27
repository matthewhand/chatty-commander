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

You can manage voice commands directly from the **WebUI**. Navigate to the **Commands** page to add, edit, or remove commands.

### Managing Commands via WebUI
1.  **View Commands**: See all configured commands in the "Commands" tab.
2.  **Add Command**: Click "New Command", specify a unique ID, choose an action type (Keypress, URL, Shell, Custom Message), and enter the payload.
3.  **Edit/Delete**: Use the action buttons on each command card to modify or remove commands.

Changes made in the WebUI are persisted to `config.json` automatically.

![Commands Page](../screenshots/commands-list-updated.png)

### Action Types
- **Keypress**: Simulates keyboard shortcuts (e.g., `ctrl+alt+t`).
- **URL**: Sends a POST request to a webhook (e.g., Home Assistant).
- **Shell**: Executes a system shell command.
- **Custom Message**: Echoes a message (useful for testing or TTS).
