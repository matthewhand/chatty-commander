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

def run_web_mode(config, model_manager, state_manager, command_executor, logger, no_auth=False):
    """Run the web UI mode with FastAPI server."""
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        import os
        import asyncio
    except ImportError:
        logger.error("FastAPI and uvicorn are required for web mode. Install with: uv add fastapi uvicorn")
        sys.exit(1)
    
    logger.info(f"Starting web mode (auth={'disabled' if no_auth else 'enabled'})")
    
    app = FastAPI(title="ChattyCommander WebUI", version="1.0.0")
    
    # Add API routes here (will be implemented)
    @app.get("/api/v1/status")
    async def get_status():
        return {
            "status": "running",
            "current_state": state_manager.current_state,
            "auth_enabled": not no_auth
        }

    @app.get("/api/v1/config")
    async def get_config():
        return config.__dict__

    @app.post("/api/v1/state")
    async def update_state(new_state: str):
        state_manager.change_state(new_state)
        await broadcast_state()
        return {"message": "State updated", "new_state": new_state}

    @app.post("/api/v1/command")
    async def execute_command_api(command: str):
        if command in config.model_actions:
            command_executor.execute_command(command)
            return {"message": "Command executed", "command": command}
        return {"error": "Invalid command"}
    
    # Serve React frontend static files
    frontend_build_path = "webui/frontend/build"
    frontend_static_path = f"{frontend_build_path}/static"
    
    if os.path.exists(frontend_build_path) and os.path.exists(frontend_static_path):
        app.mount("/static", StaticFiles(directory=frontend_static_path), name="static")
        
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            if full_path.startswith("api/"):
                return {"error": "API endpoint not found"}
            return FileResponse(f"{frontend_build_path}/index.html")
        
        logger.info(f"Serving React frontend from {frontend_build_path}")
    else:
        logger.warning(f"Frontend build not found at {frontend_build_path}. Run 'npm run build' in webui/frontend/")
        
        @app.get("/")
        async def root():
            return {
                "message": "ChattyCommander WebUI",
                "status": "Frontend build not available",
                "instructions": "Run 'npm run build' in webui/frontend/ to build the React frontend"
            }
    
    # WebSocket endpoint for real-time communication
    connections = []

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        connections.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Process incoming messages if needed
                if data == "get_state":
                    await websocket.send_text(state_manager.current_state)
                # For now, echo
                await websocket.send_text(f"Echo: {data}")
        except Exception:
            connections.remove(websocket)
            await websocket.close()

    async def broadcast_state():
        for conn in connections:
            await conn.send_text(state_manager.current_state)

    async def listening_loop():
        while True:
            command = await model_manager.async_listen_for_commands()
            if command:
                logger.info(f"Command detected: {command}")
                new_state = state_manager.update_state(command)
                if new_state:
                    logger.info(f"Transitioning to new state: {new_state}")
                    model_manager.reload_models(new_state)
                    await broadcast_state()

    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(listening_loop())

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8100, log_level="info")

def run_gui_mode(config, model_manager, state_manager, command_executor, logger):
    """Run the GUI mode."""
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
        description="ChattyCommander - Voice-activated command processing system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start in CLI voice command mode
  %(prog)s --web              # Start web UI server
  %(prog)s --web --no-auth    # Start web UI without authentication (local dev)
  %(prog)s --gui              # Start graphical interface
  %(prog)s --config           # Interactive configuration wizard

For more information, visit: https://github.com/your-repo/chatty-commander
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--web", 
        action="store_true",
        help="Start web UI server with FastAPI backend (default port: 8001)"
    )
    mode_group.add_argument(
        "--gui", 
        action="store_true",
        help="Start graphical user interface (requires GUI dependencies)"
    )
    mode_group.add_argument(
        "--config", 
        action="store_true",
        help="Launch interactive configuration wizard"
    )
    
    parser.add_argument(
        "--no-auth", 
        action="store_true",
        help="Disable authentication (INSECURE - only for local development)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8100,
        help="Port for web server (default: 8100)"
    )
    
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # If no arguments provided, could implement interactive shell here
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
        # TODO: Implement interactive configuration wizard
        print("Interactive configuration wizard not yet implemented")
        sys.exit(1)
    elif args.web:
        run_web_mode(config, model_manager, state_manager, command_executor, logger, args.no_auth)
    elif args.gui:
        run_gui_mode(config, model_manager, state_manager, command_executor, logger)
    else:
        run_cli_mode(config, model_manager, state_manager, command_executor, logger)

if __name__ == "__main__":
    main()
