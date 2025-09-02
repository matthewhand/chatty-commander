# ChattyCommander User Manual

## Introduction

ChattyCommander is a voice-activated command system that allows hands-free control of your computer and smart devices.

## Installation

1. Clone the repository: `git clone https://github.com/your-repo/chatty-commander.git`
1. Install dependencies: `uv sync`
1. Download models to models-idle/, models-computer/, models-chatty/

## Quick Start

Run the CLI: `uv run python main.py`
For GUI: `uv run python main.py --gui`
For Web: `uv run python main.py --web --no-auth`

## Configuration

Edit config.json to add custom commands.
Example:

```json
{
  "model_actions": {
    "lights_on": { "url": "http://smart-home/api/lights/on" }
  }
}
```

## Usage Examples

- Say "Hey Computer" to enter computer mode.
- Say "Lights on" to execute the command.

## Troubleshooting

- Check logs in logs/ directory.
- Ensure microphone permissions are granted.

For more details, see API.md.
