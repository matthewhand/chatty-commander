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

## Core Concepts

### Modes (States)
ChattyCommander operates in distinct "modes" or "states," each designed to activate a specific set of voice models and functionalities. This allows the application to respond differently based on the context you've set. The primary states are:

-   **Idle**: The default state. In this mode, ChattyCommander primarily listens for wake words that transition it to other states (e.g., "hey chat tee", "hey khum puter").
-   **Computer**: Once in this state, ChattyCommander activates models specifically designed for system-level commands, allowing you to control your computer through voice.
-   **Chatty**: In this mode, the application is configured to interact with chatbot models, enabling conversational commands and responses.

Transitions between these states are triggered by specific wake words defined in your configuration, ensuring that only relevant models are active at any given time.

### Actions and Keybindings
Actions are the core functionalities ChattyCommander performs in response to recognized commands. These can include:

-   **Keypresses**: Emulating keyboard shortcuts (e.g., `ctrl+shift+;` for `okay_stop`). These are handled by the `pyautogui` library.
-   **URL Calls**: Sending HTTP requests to specified URLs, often used for integrating with smart home systems like Home Assistant.
-   **System Commands**: Executing shell commands directly on your operating system.

Each recognized voice command is mapped to a specific action within the `config.py` file, allowing for flexible and customizable responses.

### Voice Files (ONNX Models)
ChattyCommander utilizes ONNX (Open Neural Network Exchange) models for efficient and accurate voice command recognition. These models are pre-trained neural networks that convert spoken words into actionable commands.

-   **Model Placement**: ONNX models are organized into specific directories (`models-idle`, `models-computer`, `models-chatty`) corresponding to the application's states.
-   **Efficiency**: ONNX models are chosen for their optimized performance, enabling real-time voice processing with minimal latency.
-   **Customization**: Users can train and integrate their own ONNX models to extend ChattyCommander's vocabulary and command recognition capabilities.

## Installation

1. **Prerequisites**: Ensure you have Python 3.11+ and `uv` installed for dependency management.
2. **Clone the Repository**: `git clone https://github.com/your-repo/chatty-commander.git`
3. **Navigate to Directory**: `cd chatty-commander`
4. **Install Dependencies**: Run `uv sync` to install all required packages. This will also make the `chatty` command available in `.venv/bin/`.
5. **Model Setup**: Place your ONNX models in the appropriate directories: `models-idle`, `models-computer`, `models-chatty`.

## Usage

### Command Line Interface

To start the application:

```bash
uv run chatty run
```

- The app will load models based on the initial 'idle' state and begin listening for voice input.
- Speak a wake word (e.g., "hey khum puter") to transition states and trigger actions.
- Logs are saved in `logs/chattycommander.log` for debugging.

For testing in environments without a display, use `xvfb-run uv run chatty run`.

### Desktop GUI Application

ChattyCommander now includes a comprehensive desktop GUI for easy configuration and management:

```bash
uv run chatty gui
```

The GUI provides:

- **Visual Configuration**: Easy-to-use interface for setting up commands, states, and models
- **Command Management**: Add, edit, and delete URL commands, keypress commands, and system commands
- **State Configuration**: Configure model associations for different states (idle, chatty, computer)
- **Model Settings**: Set model paths and inference framework preferences
- **Audio Configuration**: Adjust recording settings like sample rate and channels
- **Service Control**: Start/stop the ChattyCommander service directly from the GUI
- **Real-time Monitoring**: View service logs and status in real-time
- **Configuration Testing**: Validate your configuration before running

#### GUI Features

- **Tabbed Interface**: Organized sections for Commands, States, Models, Audio, and Service control
- **Command Types**: Support for URL commands (HTTP requests), keypress commands (keyboard shortcuts), and system commands (shell execution)
- **Live Service Management**: Start and stop the voice recognition service with real-time log monitoring
- **Configuration Import/Export**: Load and save configuration files
- **Validation**: Built-in configuration validation to catch errors before running

The GUI is optional - you can continue using the CLI-only approach if preferred. Both interfaces work with the same configuration files and provide the same functionality.

## Configuration

The application uses a JSON-based configuration system with automatic default generation.

### Default Configuration

When no configuration is detected, the system automatically generates:
- A comprehensive `config.json` with sample commands and settings
- A `wakewords/` directory containing placeholder ONNX files
- Model directories (`models-idle`, `models-computer`, `models-chatty`) with symlinks to wakeword files
- Sample actions for various modes (idle, computer, chatty)

### Configuration Files

- `config.json` - Main configuration file containing commands, keybindings, and settings
- `wakewords/` - Central directory for wakeword ONNX model files
- Model directories (`models-idle`, `models-computer`, `models-chatty`) - Contains symlinks to wakeword files for different states

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


