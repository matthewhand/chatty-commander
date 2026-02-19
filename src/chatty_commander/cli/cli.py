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

"""Entry point for the ChattyCommander application.

This module coordinates model loading, manages state transitions based on
voice commands, and handles the execution of commands.
"""

import argparse
import os
import signal
import sys
import threading

# NOTE: Intentionally avoid importing heavy modules at import time.
# Any imports of internal components are done lazily inside functions
# after we know we are not just answering --help. This keeps
# `python -m chatty_commander.main --help` lightweight and reliable in CI.

# Expose patchable module-level names that tests expect; they are populated
# lazily inside cli_main() unless patched by tests.
Config = None  # type: ignore[assignment]
ModelManager = None  # type: ignore[assignment]
StateManager = None  # type: ignore[assignment]
CommandExecutor = None  # type: ignore[assignment]
generate_default_config_if_needed = None  # type: ignore[assignment]

# setup_logger is safe/lightweight to import at import time so tests can patch it
from chatty_commander.utils.logger import setup_logger  # noqa: E402


def run_cli_mode(config, model_manager, state_manager, command_executor, logger):
    """Run the traditional CLI voice command mode with graceful shutdown."""
    logger.info("Starting CLI voice command mode")

    # Load models based on the initial idle state
    model_manager.reload_models(state_manager.current_state)

    shutdown_flag = {"stop": False}

    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_flag["stop"] = True

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while not shutdown_flag["stop"]:
            # Listen for voice input
            command = model_manager.listen_for_commands()
            if not command:
                continue

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
        logger.info("KeyboardInterrupt received; shutting down")
    finally:
        # Perform any resource cleanup if needed
        try:
            if hasattr(model_manager, "shutdown"):
                model_manager.shutdown()
            if hasattr(state_manager, "shutdown"):
                state_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        logger.info("ChattyCommander CLI shutdown complete")
        sys.exit(0)


def run_web_mode(
    config,
    model_manager,
    state_manager,
    command_executor,
    logger,
    *,
    host: str = "0.0.0.0",
    port: int = 8100,
    no_auth: bool = False,
):
    """Run the web UI mode with FastAPI server and graceful shutdown."""

    try:
        from chatty_commander.web.web_mode import WebModeServer
    except ImportError:
        logger.error(
            "Web mode dependencies not available. Install with: uv add fastapi uvicorn websockets"
        )
        sys.exit(1)

    logger.info(
        f"Starting web mode (auth={'disabled' if no_auth else 'enabled'}) on {host}:{port}"
    )

    # Create web server instance
    web_server = WebModeServer(
        config,
        state_manager,
        model_manager,
        command_executor,
        no_auth=no_auth,
    )

    # Setup callbacks for voice command integration
    def on_command_detected(command):
        web_server.on_command_detected(command)

    def on_state_change(old_state, new_state):
        web_server._on_state_change(old_state, new_state)

    # Register callbacks
    if hasattr(model_manager, "add_command_callback"):
        model_manager.add_command_callback(on_command_detected)
    if hasattr(state_manager, "add_state_change_callback"):
        state_manager.add_state_change_callback(on_state_change)

    stop_event = threading.Event()

    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, stopping web server...")
        stop_event.set()
        try:
            stopper = getattr(web_server, "stop", None)
            if callable(stopper):
                stopper()
        except Exception as e:
            logger.error(f"Error stopping web server: {e}")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    env_host = os.getenv("CHATCOMM_HOST")
    env_port = os.getenv("CHATCOMM_PORT")
    if env_host:
        host = env_host
    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            logger.warning("Invalid CHATCOMM_PORT '%s'; using %s", env_port, port)
    _log_level = os.getenv("CHATCOMM_LOG_LEVEL", "info")  # noqa: F841

    # Start the server
    try:
        web_server.run(host=host, port=port)
    finally:
        try:
            if hasattr(model_manager, "shutdown"):
                model_manager.shutdown()
            if hasattr(state_manager, "shutdown"):
                state_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during web mode shutdown: {e}")
        logger.info("Web mode shutdown complete")


def run_gui_mode(
    config,
    model_manager,
    state_manager,
    command_executor,
    logger,
    display_override: str | None = None,
    no_gui: bool = False,
):
    """Run the GUI mode with graceful handling in headless environments.

    Returns:
        int: 0 if skipped or exited cleanly; non-zero if GUI could not start due to missing deps.
    """

    if no_gui:
        logger.info("--no-gui specified; skipping GUI launch")
        return 0

    # Apply DISPLAY override if provided (POSIX only)
    if display_override and os.name != "nt":
        os.environ["DISPLAY"] = display_override

    # Graceful handling when DISPLAY is not present (headless/CI on POSIX)
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        logger.warning(
            "No DISPLAY environment variable set. Skipping GUI mode in headless environment."
        )
        return 0
    # Prefer new tray popup GUI (pystray + pywebview) with fallback to legacy tkinter GUI
    try:
        # Prefer avatar GUI if available (pywebview + local index.html)
        try:
            try:
                from chatty_commander.avatars.avatar_gui import (
                    run_avatar_gui,  # type: ignore
                )
            except Exception:
                from src.chatty_commander.avatars.avatar_gui import (
                    run_avatar_gui,  # type: ignore
                )
            logger.info("Starting Avatar GUI (TalkingHead)")
            rc = run_avatar_gui()
            return 0 if rc is None else int(rc)
        except Exception as e:
            logger.warning(
                f"Avatar GUI unavailable ({e}); falling back to PyQt5 avatar GUI"
            )
            try:
                # Try PyQt5-based transparent browser avatar
                try:
                    from chatty_commander.gui.pyqt5_avatar import (
                        run_pyqt5_avatar,  # type: ignore
                    )
                except Exception:
                    from src.chatty_commander.gui.pyqt5_avatar import (
                        run_pyqt5_avatar,  # type: ignore
                    )
                logger.info("Starting PyQt5 Avatar GUI (Transparent Browser)")
                rc = run_pyqt5_avatar(config, logger)
                return 0 if rc is None else int(rc)
            except Exception as e2:
                logger.warning(
                    f"PyQt5 Avatar GUI unavailable ({e2}); falling back to tray popup GUI"
                )
                try:
                    # Installed package path
                    from chatty_commander.gui.tray_popup import (
                        run_tray_popup,  # type: ignore
                    )
                except Exception:
                    # Repo-root execution fallback
                    from src.chatty_commander.gui.tray_popup import (
                        run_tray_popup,  # type: ignore
                    )

                logger.info("Starting GUI tray popup mode")
                rc = run_tray_popup(config, logger)
                return 0 if rc is None else int(rc)
    except Exception as e:
        logger.warning(
            f"Tray popup GUI unavailable ({e}); falling back to legacy tkinter GUI"
        )
        try:
            from chatty_commander.gui import main as gui_main

            logger.info("Starting legacy tkinter GUI mode")
            rc = gui_main()
            return 0 if rc is None else int(rc)
        except Exception:
            logger.error("GUI dependencies not available. Install with: uv add tkinter")
            return 2


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="ChattyCommander - Advanced voice-activated command processing system.\n"
        "This application allows users to control their computer using voice commands, "
        "with support for multiple modes including CLI, web UI, GUI, and configuration wizard.\n"
        "It integrates machine learning models for command detection and state management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Start in CLI voice command mode
  %(prog)s --shell            # Start interactive text shell mode
  %(prog)s --web              # Start web UI server on default port 8100
  %(prog)s --web --port 8080 --no-auth  # Start web server on port 8080 without auth
  %(prog)s --gui              # Launch graphical user interface
  %(prog)s --config           # Run interactive configuration wizard
  %(prog)s --log-level DEBUG  # Start with debug logging
  %(prog)s list               # List available commands
  %(prog)s list --json        # List commands in JSON format
  %(prog)s exec <command>     # Execute a command
  %(prog)s exec <command> --dry-run  # Show what would be executed

Available modes:
- CLI: Voice-activated command processing
- Shell: Interactive text-based command input
- Web: Browser-based interface with real-time updates
- GUI: Desktop application interface
- Config: Setup and configuration tool

For detailed documentation and source code, visit: https://github.com/your-repo/chatty-commander
        ''',
    )

    # Add subparsers for list and exec commands
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # list subcommand
    list_parser = subparsers.add_parser("list", help="List available commands")
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    # exec subcommand
    exec_parser = subparsers.add_parser("exec", help="Execute a command")
    exec_parser.add_argument(
        "command_name",
        help="Name of the command to execute",
    )
    exec_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running it",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--web",
        action="store_true",
        help="Start the web UI server using FastAPI backend. Requires FastAPI and Uvicorn. "
        "Serves a React-based frontend if built.",
    )
    mode_group.add_argument(
        "--gui",
        action="store_true",
        help="Start the graphical user interface. Requires Tkinter and a DISPLAY environment.",
    )
    mode_group.add_argument(
        "--config",
        action="store_true",
        help="Launch the interactive configuration wizard to set up models, commands, and settings.",
    )
    mode_group.add_argument(
        "--shell",
        action="store_true",
        help="Start interactive shell mode for text-based command input and execution.",
    )

    # Orchestrator flags (opt-in; does not change default behavior)
    parser.add_argument(
        "--orchestrate",
        action="store_true",
        help="Use the mode orchestrator to unify adapters (text, web, gui, wakeword, cv, discord bridge).",
    )
    parser.add_argument(
        "--enable-text",
        action="store_true",
        help="Enable text adapter in orchestrator.",
    )
    parser.add_argument(
        "--enable-openwakeword",
        action="store_true",
        help="Enable OpenWakeWord adapter in orchestrator.",
    )
    parser.add_argument(
        "--enable-computer-vision",
        action="store_true",
        help="Enable Computer Vision adapter in orchestrator.",
    )
    parser.add_argument(
        "--enable-discord-bridge",
        action="store_true",
        help="Enable Discord/Slack bridge adapter (requires advisors + bridge token).",
    )

    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication for web mode (INSECURE - use only for local development).",
    )

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Specify the host interface for the web server (default: 0.0.0.0).",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Specify the port for the web server. Only used in web mode.",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level for the application (default: INFO).",
    )

    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Avoid launching the GUI even if --gui is provided; useful in CI/headless.",
    )
    parser.add_argument(
        "--display",
        type=str,
        default=None,
        help="Override DISPLAY value for GUI mode (e.g., :0).",
    )

    # Advisors convenience flag
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in lightweight test mode (mock models, no AI core).",
    )

    return parser


def run_interactive_shell(
    config, model_manager, state_manager, command_executor, logger
):
    """Run interactive text-based shell mode with tab completion."""
    import readline

    logger.info("Starting interactive shell mode")
    print("ChattyCommander Interactive Shell")
    print("Type 'help' for commands, 'exit' to quit")

    commands = ["help", "exit", "state", "models", "execute"]
    model_actions = list(config.model_actions.keys())

    def completer(text, state):
        options = [cmd for cmd in commands if cmd.startswith(text)]
        if text.startswith("execute "):
            subtext = text[8:]
            suboptions = [
                f"execute {act}" for act in model_actions if act.startswith(subtext)
            ]
            try:
                return suboptions[state]
            except IndexError:
                return None
        try:
            return options[state]
        except IndexError:
            return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    while True:
        try:
            input_str = input("> ").strip()
            if not input_str:
                continue
            if input_str.lower() == "exit":
                break
            if input_str.lower() == "help":
                print(
                    "Available commands: help, exit, state, models, execute <command>"
                )
                continue
            if input_str.lower() == "state":
                print(f"Current state: {state_manager.current_state}")
                continue
            if input_str.lower() == "models":
                print("Loaded models: " + ", ".join(model_manager.get_models()))
                continue
            if input_str.startswith("execute "):
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


def run_orchestrator_mode(
    config, model_manager, state_manager, command_executor, logger, args
):
    """Run orchestrator-driven mode; adapters route to the same command sink."""
    # Lazy import to avoid heavy imports in --help path
    from chatty_commander.app.orchestrator import (
        ModeOrchestrator,
        OrchestratorFlags,
    )

    flags = OrchestratorFlags(
        enable_text=bool(getattr(args, "enable_text", False)),
        enable_gui=bool(getattr(args, "gui", False)),
        enable_web=bool(getattr(args, "web", False)),
        enable_openwakeword=bool(getattr(args, "enable_openwakeword", False)),
        enable_computer_vision=bool(getattr(args, "enable_computer_vision", False)),
        enable_discord_bridge=bool(getattr(args, "enable_discord_bridge", False)),
    )
    orchestrator = ModeOrchestrator(
        config=config,
        command_sink=command_executor,
        advisor_sink=None,
        flags=flags,
    )
    selected = orchestrator.start()
    logger.info(f"Orchestrator started adapters: {selected}")
    # For now, block on CLI loop to keep process alive if no web/gui
    if not args.web and not args.gui:
        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            pass
    orchestrator.stop()
    return 0


def cli_main():
    """Entry point for the ChattyCommander application."""
    parser = create_parser()
    # Parse as the very first action and immediately return argparse exit code for help/usage
    # We must allow --help to exit(0) without doing any setup, to satisfy tests.
    try:
        args, _unknown = parser.parse_known_args()
    except SystemExit as e:
        # Propagate argparse's exit code (0 on --help)
        return int(getattr(e, "code", 0) or 0)

    # If help was requested, argparse would have exited above with code 0.
    # Continue with validation for actual runs only.
    # Argument validation (only enforce when options are provided)
    if getattr(args, "web", False) and args.port is not None and args.port < 1024:
        parser.error("Port must be 1024 or higher for non-root users")
    if getattr(args, "no_auth", False) and not getattr(args, "web", False):
        parser.error("--no-auth only applicable in web mode")

    # If user only asked for help (--help), we would have already returned.
    # If no args other than program name, launch interactive shell
    if len(sys.argv) <= 1:
        print("ChattyCommander - Voice Command System")
        print("Starting interactive shell... (type 'exit' to quit)")
        # We'll launch the interactive shell after initialization
        interactive_mode = True
    elif "--help" in sys.argv or "-h" in sys.argv:
        print("ChattyCommander - Voice Command System")
        print("Use --help for available options")
        # Align with tests expecting SystemExit on main invocation path.
        raise SystemExit(0)
    else:
        interactive_mode = False

    # Ensure logger is created with the expected name for tests
    logger = setup_logger("main", "logs/chattycommander.log")
    logger.info("Starting ChattyCommander application")

    # Generate default configuration if needed
    global generate_default_config_if_needed
    if generate_default_config_if_needed is None:  # Resolve lazily unless patched
        from chatty_commander.app.default_config import (
            generate_default_config_if_needed as _gdfin,
        )

        generate_default_config_if_needed = _gdfin

    if generate_default_config_if_needed():
        logger.info("Default configuration generated")

    # Load configuration settings
    global Config
    if Config is None:  # Resolve lazily unless patched
        from chatty_commander.app.config import Config as _Config

        Config = _Config
    config = Config()
    # Apply CLI overrides to web server settings
    web_cfg = getattr(config, "web_server", {}) or {}
    if args.host is not None:
        web_cfg["host"] = args.host
    if args.port is not None:
        web_cfg["port"] = args.port
    if args.no_auth:
        web_cfg["auth_enabled"] = False
    if web_cfg:
        config.web_server = web_cfg
        try:
            config.config["web_server"] = web_cfg
        except Exception:
            pass
    # Apply runtime advisors enable if requested
    if getattr(args, "advisors", False):
        try:
            if not hasattr(config, "advisors"):
                config.advisors = {}
            config.advisors["enabled"] = True
        except Exception:
            pass

    # Derive web server settings with CLI overrides
    web_cfg = getattr(config, "web_server", {}) or {}
    host = web_cfg.get("host", "0.0.0.0")
    port = int(web_cfg.get("port", 8100))
    auth_enabled = bool(web_cfg.get("auth_enabled", True))

    if args.host is not None:
        host = args.host
    if args.port is not None:
        port = args.port
    if getattr(args, "no_auth", False):
        auth_enabled = False

    web_cfg.update({"host": host, "port": port, "auth_enabled": auth_enabled})
    config.web_server = web_cfg

    global ModelManager, StateManager, CommandExecutor
    if ModelManager is None:
        from chatty_commander.app.model_manager import ModelManager as _ModelManager

        ModelManager = _ModelManager
    if StateManager is None:
        from chatty_commander.app.state_manager import StateManager as _StateManager

        StateManager = _StateManager
    if CommandExecutor is None:
        from chatty_commander.app.command_executor import (
            CommandExecutor as _CommandExecutor,
        )

        CommandExecutor = _CommandExecutor

    model_manager = ModelManager(config, mock_models=getattr(args, "test_mode", False))
    state_manager = StateManager()
    command_executor = CommandExecutor(config, model_manager, state_manager)

    # Handle list subcommand
    if getattr(args, "subcommand", None) == "list":
        import json as json_module

        actions = getattr(config, "model_actions", {}) or {}
        if getattr(args, "json", False):
            # Output as JSON array
            result = []
            for name, action in actions.items():
                action_type = "shell" if "shell" in action else "url" if "url" in action else "unknown"
                result.append({"name": name, "type": action_type})
            print(json_module.dumps(result, indent=2))
        else:
            # Output as text
            if not actions:
                print("No commands configured.")
            else:
                print("Available commands:")
                for name in sorted(actions.keys()):
                    print(f"- {name}")
        return 0

    # Handle exec subcommand
    if getattr(args, "subcommand", None) == "exec":
        command_name = getattr(args, "command_name", None)
        dry_run = getattr(args, "dry_run", False)
        actions = getattr(config, "model_actions", {}) or {}

        if command_name not in actions:
            print(f"Unknown command: {command_name}", file=sys.stderr)
            raise SystemExit(1)

        if dry_run:
            print(f"DRY RUN: would execute command '{command_name}'")
            return 0

        # Actually execute the command
        command_executor.execute_command(command_name)
        return 0

    # Initialize AI intelligence core for enhanced conversations
    # Skip if in test mode to save resources
    if not getattr(args, "test_mode", False):
        try:
            from ..ai import create_intelligence_core

            ai_core = create_intelligence_core(config)

            # Set up AI response handling
            def handle_ai_response(response):
                print(f"AI: {response.text}")
                if response.actions:
                    print(f"Actions: {response.actions}")

            ai_core.on_response = handle_ai_response
            ai_core.on_mode_change = lambda mode: print(f"Mode changed to: {mode}")
            ai_core.on_error = lambda error: print(f"AI Error: {error}")

            print("🤖 AI Intelligence Core initialized successfully!")
            print("🎤 Enhanced voice processing available")
            print("💬 Intelligent conversation engine ready")

        except Exception as e:
            print(f"[WARN] AI Intelligence Core initialization failed: {e}")
            ai_core = None
    else:
        logger.info("Test mode enabled: AI Intelligence Core disabled.")

    # Route to appropriate mode
    if getattr(args, "config", False):
        from chatty_commander.config_cli import ConfigCLI

        config_cli = ConfigCLI()
        config_cli.run_wizard()
        return 0
    elif getattr(args, "web", False):
        # Ensure web_server config exists and reflect CLI overrides
        if not hasattr(config, "web_server") or config.web_server is None:
            config.web_server = {}
        host = getattr(args, "host", None) or config.web_server.get("host", "0.0.0.0")
        port = getattr(args, "port", None) or config.web_server.get("port", 8100)
        config.web_server.update(
            {"host": host, "port": port, "auth_enabled": not args.no_auth}
        )
        run_web_mode(
            config,
            model_manager,
            state_manager,
            command_executor,
            logger,
            host=host,
            no_auth=args.no_auth,
            port=(
                args.port
                if args.port is not None
                else getattr(getattr(config, "web_server", {}), "get", lambda *_: None)(
                    "port", 8100
                )
            ),
        )
        return 0
    elif args.gui:
        # Respect return codes from GUI runner (0=headless skipped, 2=deps missing)
        rc = run_gui_mode(
            config,
            model_manager,
            state_manager,
            command_executor,
            logger,
            display_override=args.display,
            no_gui=args.no_gui,
        )
        if isinstance(rc, int) and rc != 0:
            # Non-zero means GUI could not start; exit without stack trace
            return rc
        return 0
    elif args.shell:
        run_interactive_shell(
            config, model_manager, state_manager, command_executor, logger
        )
        return 0
    elif getattr(args, "orchestrate", False):
        return run_orchestrator_mode(
            config, model_manager, state_manager, command_executor, logger, args
        )
    elif interactive_mode:
        # Launch interactive shell when no arguments provided
        run_interactive_shell(
            config, model_manager, state_manager, command_executor, logger
        )
        return 0
    else:
        run_cli_mode(config, model_manager, state_manager, command_executor, logger)
        return 0


if __name__ == "__main__":
    sys.exit(cli_main())
