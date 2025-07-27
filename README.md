# Chatty Commander Project

This project sets up various scripts and configurations to automate the launch of multiple applications and perform network traffic capture for troubleshooting. It also includes a Python application for command extraction and execution using wake word models.

## Components

### 1. keybindings_demo.sh
This script demonstrates various keybindings and performs a mouse click to verify their functionality.

### 2. startup_apps.sh
This startup script launches the following applications:
- nvtop
- htop
- pavucontrol
- alsamixer
- Epiphany browser

Additionally, it runs tcpdump to capture network traffic for 5 minutes and then executes the keybindings demo script.

### 3. Tcpdump Capture
The tcpdump command is used to capture network traffic for 5 minutes after startup. The captured data is saved in the `tcpdump` folder with a timestamped filename for troubleshooting purposes.

### 4. Python Application
The Python components include scripts for model management, command extraction, and execution. Recent improvements:
- Switched to using `uv` for faster dependency management.
- Adjusted Python version requirements for better compatibility.
- Fixed model loading issues with `openwakeword` and updated tests accordingly.

To install dependencies, use `uv sync`.

### 5. README.md
This file provides an overview of the project and its components.

