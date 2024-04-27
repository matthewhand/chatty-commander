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
from command_executor import CommandExecutor
from state_manager import StateManager
from utils.logger import setup_logger

def main():
    logger = setup_logger(__name__)
    logger.info("Starting ChattyCommander application")

    # Load configuration settings
    config = Config()
    model_manager = ModelManager(config)
    state_manager = StateManager()
    command_executor = CommandExecutor(config, model_manager, state_manager)

    # Load models based on the initial idle state
    model_manager.load_models(state_manager.current_state)

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
                    model_manager.load_models(new_state)
                
                # Execute the detected command
                command_executor.execute_command(command)
    
    except KeyboardInterrupt:
        logger.info("Shutting down the ChattyCommander application")
        sys.exit()

if __name__ == "__main__":
    main()
