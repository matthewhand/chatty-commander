# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
main.py

This module serves as the entry point for the ChattyCommander application. It coordinates the
loading of machine learning models, manages state transitions based on voice commands, and
handles the execution of commands.

Usage:
    Run the script from the command line to start the voice-activated command processing system.
    Ensure that all dependencies are installed and models are correctly placed in their respective directories.

Example:
    python main.py
"""

import sys
from config import Config
from model_manager import ModelManager
from state_manager import StateManager
from command_executor import CommandExecutor
from utils.logger import setup_logger

try:
    from default_config import generate_default_config_if_needed
except ImportError:

    def generate_default_config_if_needed():
        return False


def main():
    logger = setup_logger(__name__, "logs/chattycommander.log")
    logger.info("Starting ChattyCommander application")

    # Generate default configuration if needed
    if generate_default_config_if_needed():
        logger.info("Default configuration generated")

    # Load configuration settings
    config = Config()
    model_manager = ModelManager(config)
    state_manager = StateManager()
    command_executor = CommandExecutor(config, model_manager, state_manager)

    # Load models based on the initial idle state
    model_manager.reload_models(state_manager.current_state)

    try:
        while True:
            # Listen for voice input
            command = model_manager.listen_for_commands()
            if command:
                logger.info(f"Command detected: {command}")

                # Update system state based on command
                new_state = state_manager.update_state(command)
                if new_state:
                    logger.info(f"Transitioning to new state: {new_state}")
                    model_manager.reload_models(new_state)

                # Execute the detected command if it's actionable
                if command in config.model_actions:
                    command_executor.execute_command(command)

    except KeyboardInterrupt:
        logger.info("Shutting down the ChattyCommander application")
        sys.exit()


if __name__ == "__main__":
    main()
