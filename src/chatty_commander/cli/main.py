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
import logging

# Ensure src/ is on sys.path so root execution finds package modules without PYTHONPATH
import os as _os
import signal
import sys
import sys as _sys
import threading

# Fix sys.path to include the project src root (two levels up from this package directory)
_pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
_root_src = _os.path.abspath(_os.path.join(_pkg_dir, "..", ".."))
if _root_src not in _sys.path:
    _sys.path.insert(0, _root_src)

# NOTE: Intentionally avoid importing heavy modules at import time.
# Any imports of internal components are done lazily inside functions
# after we know we are not just answering --help. This keeps
# `python -m chatty_commander.main --help` lightweight and reliable in CI.

# Expose patchable module-level names that tests expect; they are populated
# lazily inside main() unless patched by tests.
Config = None  # type: ignore[assignment]
ModelManager = None  # type: ignore[assignment]
StateManager = None  # type: ignore[assignment]
CommandExecutor = None  # type: ignore[assignment]
generate_default_config_if_needed = None  # type: ignore[assignment]

# setup_logger is safe/lightweight to import at import time so tests can patch it
from chatty_commander.utils.logger import setup_logger  # noqa: E402


def run_cli_mode(config, model_manager, state_manager, command_executor, logger):
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
    # Return (instead of sys.exit(0)) so the caller (main) owns the exit code;
    # the cleanup above runs via finally regardless of how the loop ended.
    return 0


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
    import os

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

    # Fail fast (web-scoped) when web_server.auth_enabled is explicitly on but
    # no API key is configured — otherwise every /api request would 401. The
    # --no-auth bypass disables the gate, so reflect that before validating.
    if no_auth and isinstance(getattr(config, "web_server", None), dict):
        config.web_server["auth_enabled"] = False
    from chatty_commander.app.env_validation import (
        EnvValidationError,
        validate_startup_env,
    )

    try:
        validate_startup_env(config, log=logger, for_web=True)
    except EnvValidationError as e:
        logger.error(str(e))
        print(str(e), file=sys.stderr)
        sys.exit(1)

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
        web_server.on_command_detected(command, confidence=1.0)

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
    env_log_level = os.getenv("CHATCOMM_LOG_LEVEL")
    if env_log_level:
        level = logging.getLevelName(env_log_level.strip().upper())
        if isinstance(level, int):
            logger.setLevel(level)
            logging.getLogger().setLevel(level)
        else:
            logger.warning(
                "Invalid CHATCOMM_LOG_LEVEL '%s'; keeping current level",
                env_log_level,
            )

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

    Delegates to the maintained implementation in cli.cli (which has the
    correct avatar -> PyQt5 -> tray popup -> legacy tkinter fallback chain),
    mirroring how run_web_mode is delegated above.

    Returns:
        int: 0 if skipped or exited cleanly; non-zero if GUI could not start due to missing deps.
    """
    from chatty_commander.cli.cli import run_gui_mode as _run_gui_mode

    return _run_gui_mode(
        config,
        model_manager,
        state_manager,
        command_executor,
        logger,
        display_override=display_override,
        no_gui=no_gui,
    )


def create_parser():
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
        """,
    )

    # Subcommands (pure-utility; dispatched before any heavy init in main()).
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # dograh subcommand group (integration utilities). register_dograh_subparser
    # only imports argparse/json/sys, so this keeps --help lightweight.
    from chatty_commander.cli.dograh_cli import register_dograh_subparser

    register_dograh_subparser(subparsers)

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

    # Advisors enable flag (opt-in; turns on the advisors subsystem at runtime).
    parser.add_argument(
        "--advisors",
        action="store_true",
        help="Enable the advisors subsystem (LLM agents) at runtime, overriding config.",
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

    # Headless-friendly switches
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
                # get_models(state) requires a state arg; list every loaded model
                # across all states (mirrors the interactive shell in cli.py).
                all_models = [
                    name
                    for state_models in model_manager.models.values()
                    for name in state_models.keys()
                ]
                print("Loaded models: " + ", ".join(all_models))
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

    # Shared with cli.cli: builds an AdvisorsService sink when advisors are
    # enabled, logging a warning and returning None on construction failure.
    from chatty_commander.cli.cli import build_advisor_sink

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
        advisor_sink=build_advisor_sink(config, logger),
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


def main():
    """Entry point for the ChattyCommander application."""
    # `list` and `exec` are pure-utility subcommands fully implemented in
    # cli.cli. Delegate to it so `python -m chatty_commander.cli.main list/exec`
    # behaves like the console_script instead of falling through to mode startup
    # (which loads the full ONNX pipeline and hangs in non-interactive use).
    if len(sys.argv) > 1 and sys.argv[1] in ("list", "exec"):
        from chatty_commander.cli.cli import cli_main

        return cli_main()

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
    if args.port is not None:
        # Reject anything outside the valid TCP range unconditionally (0,
        # negatives, and > 65535 are never serviceable regardless of mode).
        if not (1 <= args.port <= 65535):
            parser.error("Port must be between 1 and 65535")
        # Privileged ports (< 1024) are additionally rejected in web mode.
        if getattr(args, "web", False) and args.port < 1024:
            parser.error("Port must be 1024 or higher for non-root users")
    if getattr(args, "no_auth", False) and not getattr(args, "web", False):
        parser.error("--no-auth only applicable in web mode")

    # Dograh subcommands are pure utilities: dispatch them immediately after
    # parsing, before logger/config/model-manager init, so they never trigger
    # model loading, state-manager init, or wake-word detection.
    if getattr(args, "subcommand", None) == "dograh":
        from chatty_commander.cli.dograh_cli import handle_dograh

        return handle_dograh(args)

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

    # Fail fast when required env vars for explicitly enabled features are
    # missing (ROADMAP "Secrets validation at startup"). The config wizard is
    # exempt so users can still run it to fix their setup.
    if not getattr(args, "config", False):
        from chatty_commander.app.env_validation import (
            EnvValidationError,
            validate_startup_env,
        )

        try:
            validate_startup_env(config, log=logger)
        except EnvValidationError as e:
            logger.error(str(e))
            print(str(e), file=sys.stderr)
            return 1

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
        # host/port/auth_enabled were already derived above (single override
        # pass) honoring config-file values, CLI flags, and --no-auth. Reuse
        # them here instead of recomputing — in particular do NOT recompute
        # auth_enabled as `not args.no_auth`, which would silently re-enable
        # auth that a config file disabled.
        # Use the maintained implementation (the local stub was stale/duplicate)
        from chatty_commander.cli.cli import run_web_mode as run_web_mode
        run_web_mode(
            config,
            model_manager,
            state_manager,
            command_executor,
            logger,
            host=host,
            no_auth=args.no_auth,
            port=int(port),
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
    sys.exit(main())
