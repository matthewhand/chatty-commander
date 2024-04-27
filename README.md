# chatty-commander
Python wrapper for openWakeWord to perform system and network interactions.

```
# ChattyCommander

## Overview
ChattyCommander is a voice-activated command processing system designed to execute a variety of actions based on detected wakewords. It leverages advanced audio processing and machine learning models to recognize and respond to specific voice commands effectively.

## Prerequisites
- Windows with DirectML GPU or a Raspberry Pi CPU.
- Python 3.x installed.
- Necessary libraries installed from the `requirements.txt` file.
- Models placed in the appropriate directories within the `models/` folder.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/matthewhand/chatty-commander.git
   ```
2. Navigate to the project directory:
   ```
   cd ChattyCommander
   ```
3. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```
4. Ensure that `openwakeword` and `whispering-desktop` are configured with your OpenAI API key.

## Configuration

### Setting Up Environment Variables

1. **Create Environment File:**
   - Copy the `.env.template` file to a new file named `.env` in the same directory:
     ```
     cp .env.template .env
     ```
   - Fill in the values in the `.env` file with your actual credentials and configurations.

2. **Load Environment Variables:**
   - Ensure that your environment variables are loaded when the application starts. You can use libraries like `python-dotenv` to easily load these settings in your application.

### Example of Loading Environment Variables in Python

Install the `python-dotenv` package if you haven't already:

```bash
pip install python-dotenv

## Usage
Run the main application:
```
python chattycommander/main.py
```
This will start the system and begin listening for predefined wakewords using the models specified in the configuration files.

## Directory Structure
- **chattycommander/**: Contains all the source files.
  - **main.py**: Entry point of the application.
  - **config.py**: Configuration settings and constants.
  - **model_manager.py**: Manages loading and handling of models.
  - **command_executor.py**: Handles the execution of commands.
  - **state_manager.py**: Manages state transitions and current state.
- **models/**: Contains machine learning models categorized by their function.
  - **general/**: General voice command models.
  - **system/**: System control command models.
  - **chat/**: Interactive and conversational command models.
- **tests/**: Contains tests for the application.
- **docs/**: Documentation files.
- **scripts/**: Useful scripts for setup or maintenance.
- **requirements.txt**: List of dependencies.

## Features
- **Voice Activation**: Responds to voice commands using ONNX models.
- **State Management**: Switches between different states like idle, computer control, and chat mode based on the context of the interaction.
- **Command Execution**: Executes system commands, controls devices, or sends HTTP requests based on the recognized commands.

## Contributing
Contributions to ChattyCommander are welcome! Please refer to the CONTRIBUTING.md for more details on how to submit pull requests, file issues, and improve documentation.

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
Your Name - email@example.com
Project Link: https://github.com/matthewhand/chatty-commander
```
