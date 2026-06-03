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

## Listing and Running Commands from the CLI

You can inspect and execute configured commands directly from the terminal:

```bash
# List all configured commands
chatty-commander list

# Machine-readable output (keypress/url/shell actions are classified by type)
chatty-commander list --json

# Run a command by name
chatty-commander exec <command>

# Abort the command if it runs longer than N seconds (exits with code 1 on overrun)
chatty-commander exec <command> --timeout <seconds>
```

These subcommands are also reachable through the module entry point, which behaves
identically to the `chatty-commander` console script:

```bash
python -m chatty_commander.cli.main list
python -m chatty_commander.cli.main exec <command>
```

## Testing the Voice Pipeline

Use the `voice test` subcommand to exercise the voice pipeline without going through
the full wake-word flow:

```bash
chatty-commander voice test
```
