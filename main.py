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
import argparse
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

def run_cli_mode(config, model_manager, state_manager, command_executor, logger):
    """Run the traditional CLI voice command mode."""
    logger.info("Starting CLI voice command mode")
    
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

def run_web_mode(config, model_manager, state_manager, command_executor, logger, no_auth=False, port=8100):
    """Run the web UI mode with FastAPI server."""
    try:
        from web_mode import create_web_server
    except ImportError:
        logger.error("Web mode dependencies not available. Install with: uv add fastapi uvicorn websockets")
        sys.exit(1)
    
    logger.info(f"Starting web mode (auth={'disabled' if no_auth else 'enabled'}) on port {port}")
    
    # Create web server instance
    web_server = create_web_server(
        config_manager=config,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=no_auth
    )
    
    # Setup callbacks for voice command integration
    def on_command_detected(command):
        web_server.on_command_detected(command)
    
    def on_state_change(old_state, new_state):
        web_server._on_state_change(old_state, new_state)
    
    # Register callbacks
    if hasattr(model_manager, 'add_command_callback'):
        model_manager.add_command_callback(on_command_detected)
    if hasattr(state_manager, 'add_state_change_callback'):
        state_manager.add_state_change_callback(on_state_change)
    
    # Start the server
    web_server.run(host="0.0.0.0", port=port, log_level="info")

def run_gui_mode(config, model_manager, state_manager, command_executor, logger):
    """Run the GUI mode."""
    import os
    if 'DISPLAY' not in os.environ:
        logger.error("No DISPLAY environment variable set. GUI mode requires a graphical environment.")
        sys.exit(1)
    try:
        from gui import main as gui_main
        logger.info("Starting GUI mode")
        gui_main()
    except ImportError:
        logger.error("GUI dependencies not available. Install with: uv add tkinter")
        sys.exit(1)

def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="ChattyCommander - Advanced voice-activated command processing system.\n"
                    "This application allows users to control their computer using voice commands, "
                    "with support for multiple modes including CLI, web UI, GUI, and configuration wizard.\n"
                    "It integrates machine learning models for command detection and state management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start in CLI voice command mode
  %(prog)s --shell            # Start interactive text shell mode
  %(prog)s --web              # Start web UI server on default port 8100
  %(prog)s --web --port 8080 --no-auth  # Start web server on port 8080 without auth
  %(prog)s --gui              # Launch graphical user interface
  %(prog)s --config           # Run interactive configuration wizard
  %(prog)s --log-level DEBUG  # Start with debug logging

Available modes:
- CLI: Voice-activated command processing
- Shell: Interactive text-based command input
- Web: Browser-based interface with real-time updates
- GUI: Desktop application interface
- Config: Setup and configuration tool

For detailed documentation and source code, visit: https://github.com/your-repo/chatty-commander
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--web", 
        action="store_true",
        help="Start the web UI server using FastAPI backend. Requires FastAPI and Uvicorn. "
             "Serves a React-based frontend if built."
    )
    mode_group.add_argument(
        "--gui", 
        action="store_true",
        help="Start the graphical user interface. Requires Tkinter and a DISPLAY environment."
    )
    mode_group.add_argument(
        "--config", 
        action="store_true",
        help="Launch the interactive configuration wizard to set up models, commands, and settings."
    )
    mode_group.add_argument(
        "--shell",
        action="store_true",
        help="Start interactive shell mode for text-based command input and execution."
    )
    
    parser.add_argument(
        "--no-auth", 
        action="store_true",
        help="Disable authentication for web mode (INSECURE - use only for local development)."
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8100,
        help="Specify the port for the web server (default: 8100). Only used in web mode."
    )
    
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level for the application (default: INFO)."
    )
    
    return parser

def run_interactive_shell(config, model_manager, state_manager, command_executor, logger):
    """Run interactive text-based shell mode with tab completion."""
    import readline
    logger.info("Starting interactive shell mode")
    print("ChattyCommander Interactive Shell")
    print("Type 'help' for commands, 'exit' to quit")
    
    commands = ['help', 'exit', 'state', 'models', 'execute']
    model_actions = list(config.model_actions.keys())
    
    def completer(text, state):
        options = [cmd for cmd in commands if cmd.startswith(text)]
        if text.startswith('execute '):
            subtext = text[8:]
            suboptions = [f'execute {act}' for act in model_actions if act.startswith(subtext)]
            try:
                return suboptions[state]
            except IndexError:
                return None
        try:
            return options[state]
        except IndexError:
            return None
    
    readline.set_completer(completer)
    readline.parse_and_bind('tab: complete')
    
    while True:
        try:
            input_str = input("> ").strip()
            if not input_str:
                continue
            if input_str.lower() == 'exit':
                break
            if input_str.lower() == 'help':
                print("Available commands: help, exit, state, models, execute <command>")
                continue
            if input_str.lower() == 'state':
                print(f"Current state: {state_manager.current_state}")
                continue
            if input_str.lower() == 'models':
                print("Loaded models: " + ", ".join(model_manager.get_models()))
                continue
            if input_str.startswith('execute '):
                command = input_str[8:].strip()
                if command in config.model_actions:
                    command_executor.execute_command(command)
                    print(f"Executed: {command}")
                else:
                    print(f"Unknown command: {command}")
                continue
            
            # Treat as voice command simulation
            new_state = state_manager.update_state(input_str)
            if new_state:
                logger.info(f"Transitioning to new state: {new_state}")
                model_manager.reload_models(new_state)
            if input_str in config.model_actions:
                command_executor.execute_command(input_str)
        except EOFError:
            break
    logger.info("Exiting interactive shell")

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Argument validation
    if args.web and args.port < 1024:
        parser.error("Port must be 1024 or higher for non-root users")
    if args.no_auth and not args.web:
        parser.error("--no-auth only applicable in web mode")
    
    if len(sys.argv) == 1:
        print("ChattyCommander - Voice Command System")
        print("Use --help for available options")
        print("Starting CLI voice command mode...\n")
    
    logger = setup_logger(__name__, 'logs/chattycommander.log')
    logger.info("Starting ChattyCommander application")

    # Generate default configuration if needed
    if generate_default_config_if_needed():
        logger.info("Default configuration generated")

    # Load configuration settings
    config = Config()
    model_manager = ModelManager(config)
    state_manager = StateManager()
    command_executor = CommandExecutor(config, model_manager, state_manager)
    
    # Route to appropriate mode
    if args.config:
        from config_cli import ConfigCLI
        config_cli = ConfigCLI()
        config_cli.run_wizard()
    elif args.web:
        run_web_mode(config, model_manager, state_manager, command_executor, logger, args.no_auth, args.port)
    elif args.gui:
        run_gui_mode(config, model_manager, state_manager, command_executor, logger)
    elif args.shell:
        run_interactive_shell(config, model_manager, state_manager, command_executor, logger)
    else:
        run_cli_mode(config, model_manager, state_manager, command_executor, logger)

if __name__ == "__main__":
    main()
