# Welcome to ChattyCommander

## Introduction

Hello and welcome to ChattyCommander! If you're new here or revisiting after some time, this README will guide you through what the app does, its benefits, and how to get started. ChattyCommander is a voice-activated command processing system that uses machine learning models to detect wake words and execute predefined actions, making hands-free computing a reality.

## What It Does

ChattyCommander listens continuously for voice commands using ONNX-based models. It supports different states (idle, computer, chatty) and transitions between them based on detected wake words like "hey chat tee" or "hey khum puter". Once in a specific state, it can execute actions such as keypresses, API calls to home assistants, or interactions with chatbots.

## Benefits

- **Hands-Free Operation**: Control your computer or smart home devices using voice commands without touching the keyboard or mouse.
- **Customizable**: Easily configure models, states, and actions via `config.py` to fit your needs.
- **Integration**: Seamlessly integrates with external services like Home Assistant for smart home control or chatbots for interactive responses.
- **Efficient**: Uses efficient ML models for low-latency detection, suitable for real-time applications.

## Installation

1. **Prerequisites**: Ensure you have Python 3.11+ and `uv` installed for dependency management.
2. **Clone the Repository**: `git clone https://github.com/your-repo/chatty-commander.git`
3. **Navigate to Directory**: `cd chatty-commander`
4. **Install Dependencies**: Run `uv sync` to install all required packages. This will also make the `chatty` command available in `.venv/bin/`.
5. **Model Setup**: Place your ONNX models in the appropriate directories: `models-idle`, `models-computer`, `models-chatty`.

## Usage

To start the application:

```bash
uv run chatty run
```

- The app will load models based on the initial 'idle' state and begin listening for voice input.
- Speak a wake word (e.g., "hey khum puter") to transition states and trigger actions.
- Logs are saved in `logs/chattycommander.log` for debugging.

For testing in environments without a display, use `xvfb-run uv run chatty run`.

## Configuration

ChattyCommander can be configured dynamically using the CLI tool via the `chatty` command. This allows you to update `config.json` interactively or non-interactively.

### Interactive Mode
Run:
```bash
uv run chatty config
```
Follow the prompts to set model-action mappings, state-model associations, and other settings.

### Non-Interactive Mode
Update specific settings directly:
```bash
uv run chatty config --model-action "okay_stop" "ctrl+shift+;"
```
Use `uv run chatty config --help` for more options.

Alternatively, edit `config.py` manually for static changes.
- Model paths and state associations.
- Actions for commands (e.g., keypresses or URLs).
- Audio settings like sample rate.

## Troubleshooting

- If models fail to load, check paths in `config.py`.
- For audio issues, verify microphone settings.
- Refer to logs for detailed error messages.

Enjoy using ChattyCommander! If you have questions, feel free to open an issue.

