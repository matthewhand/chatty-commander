#!/usr/bin/env python3

import sys
import argparse
import os

class HelpfulArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Custom error message with actionable suggestions
        self.print_usage(sys.stderr)
        print(f"\nError: {message}\n", file=sys.stderr)
        print("Tip: Use '--help' after any command or subcommand for detailed options and examples.", file=sys.stderr)
        sys.exit(2)

# Set DISPLAY environment variable if not set (for GUI applications)
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

from config_cli import ConfigCLI
from main import main as run_app
from config import Config

def config_func(args):
    cli = ConfigCLI()
    # Check for wizard subcommand
    if hasattr(args, "config_subcommand") and args.config_subcommand == "wizard":
        cli.run_wizard()
    elif args.interactive:
        cli.interactive_mode()
    elif args.list:
        cli.list_config()
    elif args.set_model_action:
        cli.set_model_action(args.set_model_action[0], args.set_model_action[1])
    elif args.set_state_model:
        cli.set_state_model(args.set_state_model[0], args.set_state_model[1])
    elif args.set_listen_for:
        cli.set_listen_for(args.set_listen_for[0], args.set_listen_for[1])
    elif args.set_mode:
        cli.set_mode(args.set_mode[0], args.set_mode[1])
    else:
        print('Invalid config command. Use --help for options.')
        sys.exit(1)

def system_func(args):
    """Handle system management commands."""
    config = Config()
    
    if args.system_command == 'start-on-boot':
        if args.boot_action == 'enable':
            try:
                config.set_start_on_boot(True)
                print("Start on boot enabled successfully.")
            except Exception as e:
                print(f"Error enabling start on boot: {e}")
                sys.exit(1)
        elif args.boot_action == 'disable':
            try:
                config.set_start_on_boot(False)
                print("Start on boot disabled successfully.")
            except Exception as e:
                print(f"Error disabling start on boot: {e}")
                sys.exit(1)
        elif args.boot_action == 'status':
            status = "enabled" if config.start_on_boot else "disabled"
            print(f"Start on boot is {status}.")
    
    elif args.system_command == 'updates':
        if args.update_action == 'check':
            print("Checking for updates...")
            update_info = config.perform_update_check()
            if update_info is None:
                print("Could not check for updates.")
            elif update_info['updates_available']:
                print(f"Updates available: {update_info['update_count']} commits")
                print(f"Latest: {update_info['latest_commit']}")
            else:
                print("No updates available.")
        elif args.update_action == 'enable-auto-check':
            config.set_check_for_updates(True)
            print("Automatic update checking enabled.")
        elif args.update_action == 'disable-auto-check':
            config.set_check_for_updates(False)
            print("Automatic update checking disabled.")

def gui_command():
    """Launch the desktop GUI application."""
    try:
        # Import and run the GUI module
        import subprocess
        import sys
        result = subprocess.run([sys.executable, 'gui.py'], cwd=os.getcwd())
        return result.returncode
    except ImportError as e:
        print(f"Error: GUI dependencies not available: {e}")
        print("Please ensure tkinter is installed.")
        return 1
    except Exception as e:
        print(f"Error launching GUI: {e}")
        return 1

def cli_main():
    parser = HelpfulArgumentParser(
        description=(
            "ChattyCommander CLI\n"
            "\n"
            "A command-line interface for managing, configuring, and running the ChattyCommander application.\n"
            "Supports running the main app, launching the GUI, managing configuration, and system-level operations.\n"
            "\n"
            "Use the '--help' flag after any command or subcommand to see detailed options and descriptions.\n"
        ),
        epilog=(
            "Usage Examples:\n"
            "  Run the main application:\n"
            "    chatty-commander run\n"
            "  Run with a specific display:\n"
            "    chatty-commander run --display :1\n"
            "  Launch the GUI:\n"
            "    chatty-commander gui\n"
            "  List current configuration:\n"
            "    chatty-commander config --list\n"
            "  Set a model action:\n"
            "    chatty-commander config --set-model-action gpt4 summarize\n"
            "  Enable start on boot:\n"
            "    chatty-commander system start-on-boot enable\n"
            "  Check for updates:\n"
            "    chatty-commander system updates check\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(
        dest='command',
        required=False,
        help='Top-level command to execute. Use one of the available commands below.'
    )

    # Run subcommand
    run_parser = subparsers.add_parser(
        'run',
        help='Run the ChattyCommander application (main voice/AI assistant).',
        description=(
            "Run the main ChattyCommander application.\n"
            "This will start the voice/AI assistant in the current environment."
        )
    )
    run_parser.add_argument(
        '--display',
        type=str,
        default=None,
        help=(
            "Override the DISPLAY environment variable for GUI operations (e.g., :0, :1).\n"
            "Useful if running on a system with multiple X11 displays or remote sessions."
        )
    )
    run_parser.set_defaults(func=run_app)

    # GUI subcommand
    gui_parser = subparsers.add_parser(
        'gui',
        help='Launch the desktop GUI application.',
        description=(
            "Launch the graphical user interface for ChattyCommander.\n"
            "Requires a graphical environment and tkinter dependencies."
        )
    )
    gui_parser.set_defaults(func=lambda args: gui_command())

    # Config subcommand
    config_parser = subparsers.add_parser(
        'config',
        help='Configure the application (models, states, modes, etc).',
        description=(
            "Manage and inspect ChattyCommander configuration.\n"
            "Allows listing, setting, and interactively editing configuration options."
        )
    )
    config_parser.add_argument(
        '--list',
        action='store_true',
        help='List the current configuration values for all settings.'
    )
    config_parser.add_argument(
        '--set-model-action',
        nargs=2,
        metavar=('MODEL', 'ACTION'),
        help=(
            "Set the action for a specific model.\n"
            "MODEL: The model name (e.g., gpt4, whisper).\n"
            "ACTION: The action to assign (e.g., summarize, transcribe)."
        )
    )
    config_parser.add_argument(
        '--set-state-model',
        nargs=2,
        metavar=('STATE', 'MODELS'),
        help=(
            "Set the models for a given state.\n"
            "STATE: The state name (e.g., idle, listening).\n"
            "MODELS: Comma-separated list of models to use for this state."
        )
    )
    config_parser.add_argument(
        '--set-listen-for',
        nargs=2,
        metavar=('KEY', 'VALUE'),
        help=(
            "Set what the system should listen for.\n"
            "KEY: The listen key (e.g., wakeword, command).\n"
            "VALUE: The value to listen for (e.g., 'Hey Chatty')."
        )
    )
    config_parser.add_argument(
        '--set-mode',
        nargs=2,
        metavar=('MODE', 'VALUE'),
        help=(
            "Set options for a specific mode.\n"
            "MODE: The mode name (e.g., voice, text).\n"
            "VALUE: The value to set for the mode."
        )
    )
    config_parser.add_argument(
        '--interactive',
        action='store_true',
        help=(
            "Run the configuration tool in interactive mode.\n"
            "Allows step-by-step guided configuration via prompts."
        )
    )

    # Add 'wizard' subcommand to config
    config_subparsers = config_parser.add_subparsers(
        dest='config_subcommand',
        required=False,
        help='Config subcommand to execute.'
    )
    wizard_parser = config_subparsers.add_parser(
        'wizard',
        help='Launch the guided configuration wizard.',
        description=(
            "Start an interactive wizard to guide you through all key configuration options.\n"
            "Prompts for each option, validates input, and writes to the config file."
        )
    )

    config_parser.set_defaults(func=config_func)
    
    # System management subcommands
    system_parser = subparsers.add_parser(
        'system',
        help='System management commands (start on boot, updates, etc).',
        description=(
            "Perform system-level management tasks for ChattyCommander.\n"
            "Includes enabling/disabling start on boot and managing updates."
        )
    )
    system_subparsers = system_parser.add_subparsers(
        dest='system_command',
        required=True,
        help='System management command to execute.'
    )
    
    # Start on boot commands
    boot_parser = system_subparsers.add_parser(
        'start-on-boot',
        help='Manage whether ChattyCommander starts automatically on system boot.',
        description=(
            "Enable, disable, or check the status of automatic startup on system boot."
        )
    )
    boot_subparsers = boot_parser.add_subparsers(
        dest='boot_action',
        required=True,
        help='Action to perform for start-on-boot management.'
    )
    boot_subparsers.add_parser(
        'enable',
        help='Enable ChattyCommander to start automatically on system boot.'
    )
    boot_subparsers.add_parser(
        'disable',
        help='Disable automatic start on boot for ChattyCommander.'
    )
    boot_subparsers.add_parser(
        'status',
        help='Show whether start on boot is currently enabled or disabled.'
    )
    
    # Update commands
    update_parser = system_subparsers.add_parser(
        'updates',
        help='Manage application updates (check, enable/disable auto-check).',
        description=(
            "Check for available updates or manage automatic update checking."
        )
    )
    update_subparsers = update_parser.add_subparsers(
        dest='update_action',
        required=True,
        help='Update management action to perform.'
    )
    update_subparsers.add_parser(
        'check',
        help='Check for available updates to ChattyCommander.'
    )
    update_subparsers.add_parser(
        'enable-auto-check',
        help='Enable automatic checking for updates at startup.'
    )
    update_subparsers.add_parser(
        'disable-auto-check',
        help='Disable automatic update checking at startup.'
    )
    
    system_parser.set_defaults(func=system_func)

    import shlex
    import readline

    def cli_shell():
        import re

        print("ChattyCommander Interactive Shell")
        print("Type 'help' for available commands, 'exit' or 'quit' to leave.\n")

        # --- TAB COMPLETION SETUP ---
        # Build command tree from argparse
        def get_command_tree():
            tree = {}
            # Top-level commands
            for action in getattr(parser._subparsers, "_actions", []):
                if not hasattr(action, 'choices') or action.choices is None:
                    continue
                for cmd, subparser in action.choices.items():
                    tree[cmd] = {
                        'subparsers': {},
                        'options': [opt for opt in getattr(subparser, "_option_string_actions", {}).keys() if opt.startswith('-')]
                    }
                    # Check for subparsers (e.g., system)
                    for subaction in getattr(subparser, "_actions", []):
                        if isinstance(subaction, argparse._SubParsersAction) and getattr(subaction, "choices", None):
                            for subcmd, subsubparser in subaction.choices.items():
                                tree[cmd]['subparsers'][subcmd] = {
                                    'subparsers': {},
                                    'options': [opt for opt in getattr(subsubparser, "_option_string_actions", {}).keys() if opt.startswith('-')]
                                }
                                # Check for further subparsers (e.g., boot_action, update_action)
                                for subsubaction in getattr(subsubparser, "_actions", []):
                                    if isinstance(subsubaction, argparse._SubParsersAction) and getattr(subsubaction, "choices", None):
                                        for subsubcmd, subsubsubparser in subsubaction.choices.items():
                                            tree[cmd]['subparsers'][subcmd]['subparsers'][subsubcmd] = {
                                                'options': [opt for opt in getattr(subsubsubparser, "_option_string_actions", {}).keys() if opt.startswith('-')]
                                            }
            return tree

        command_tree = get_command_tree()

        def get_completions(text, line, begidx, endidx):
            tokens = shlex.split(line[:begidx])
            # If cursor is at a space, add an empty token
            if line and line[begidx-1:begidx] == ' ':
                tokens.append('')
            # No tokens: suggest top-level commands
            if not tokens:
                return list(command_tree.keys())
            # Top-level command
            cmd = tokens[0]
            if cmd in ("exit", "quit", "help"):
                return []
            if len(tokens) == 1:
                # Completing the command itself
                return [c for c in command_tree.keys() if c.startswith(text)]
            # Handle subcommands/options
            if cmd in command_tree:
                # If next token is a subcommand (e.g., system start-on-boot)
                if command_tree[cmd]['subparsers']:
                    if len(tokens) == 2:
                        return [sc for sc in command_tree[cmd]['subparsers'].keys() if sc.startswith(text)]
                    subcmd = tokens[1]
                    if subcmd in command_tree[cmd]['subparsers']:
                        # Third level (e.g., system start-on-boot enable)
                        if command_tree[cmd]['subparsers'][subcmd]['subparsers']:
                            if len(tokens) == 3:
                                return [ssc for ssc in command_tree[cmd]['subparsers'][subcmd]['subparsers'].keys() if ssc.startswith(text)]
                            # No further completion for deeper levels
                        # Suggest options for subcommand
                        opts = command_tree[cmd]['subparsers'][subcmd]['options']
                        return [o for o in opts if o.startswith(text)]
                # Suggest options for top-level command
                opts = command_tree[cmd]['options']
                return [o for o in opts if o.startswith(text)]
            # Fallback: no completions
            return []

        def completer(text, state):
            import readline
            line = readline.get_line_buffer()
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            completions = get_completions(text, line, begidx, endidx)
            completions = sorted(set(completions))
            if state < len(completions):
                return completions[state]
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

        while True:
            try:
                line = input("chatty> ").strip()
                if not line:
                    continue
                if line in ("exit", "quit"):
                    print("Exiting shell.")
                    break
                if line == "help":
                    parser.print_help()
                    continue
                try:
                    shell_args = shlex.split(line)
                except ValueError as ve:
                    print(f"Error parsing input: {ve}")
                    continue
                try:
                    args = parser.parse_args(shell_args)
                    if getattr(args, "command", None) is None:
                        parser.print_help()
                        continue
                    try:
                        validate_args(args)
                    except SystemExit:
                        continue
                    if args.command == 'run':
                        if getattr(args, "display", None) is not None:
                            os.environ['DISPLAY'] = args.display
                        args.func()
                    elif args.command == 'gui':
                        args.func(args)
                    elif args.command == 'system':
                        args.func(args)
                    else:
                        args.func(args)
                except SystemExit as e:
                    # argparse throws SystemExit on error; catch and print
                    pass
                except Exception as e:
                    print(f"Error: {e}")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting shell.")
                break

    if len(sys.argv) == 1:
        cli_shell()
        sys.exit(0)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    validate_args(args)
    if args.command == 'run':
        if args.display is not None:
            import os
            os.environ['DISPLAY'] = args.display
        args.func()
    elif args.command == 'gui':
        args.func(args)
    elif args.command == 'system':
        args.func(args)
    else:
        args.func(args)

def validate_args(args, config=None):
    """
    Validate CLI arguments and print actionable error messages with suggestions.
    """
    import os

    # Only load config if not provided
    if config is None:
        try:
            from config import Config
            config = Config()
        except Exception:
            config = None

    # Helper: print error and exit
    def fail(msg, suggestions=None):
        print(f"\nError: {msg}", file=sys.stderr)
        if suggestions:
            print("Valid values:", ", ".join(suggestions), file=sys.stderr)
        print("Tip: Use '--help' for more info.", file=sys.stderr)
        sys.exit(2)

    # Validate config subcommands
    if getattr(args, "command", None) == "config":
        # Validate --set-model-action
        if getattr(args, "set_model_action", None):
            model, action = args.set_model_action
            valid_models = set()
            if config:
                # Gather all models from state_models and model directories
                for models in config.state_models.values():
                    valid_models.update(models)
                for path in [config.general_models_path, config.system_models_path, config.chat_models_path]:
                    if os.path.exists(path):
                        valid_models.update([f.replace('.onnx','') for f in os.listdir(path) if f.endswith('.onnx')])
            if valid_models and model not in valid_models:
                fail(f"Invalid model name '{model}' for --set-model-action.", sorted(valid_models))
            valid_actions = {"summarize", "transcribe", "keypress", "url", "custom_message"}
            if config and config.model_actions:
                for v in config.model_actions.values():
                    if isinstance(v, dict):
                        valid_actions.update(v.keys())
                    elif isinstance(v, str):
                        valid_actions.add(v)
            if action not in valid_actions:
                fail(f"Invalid action '{action}' for --set-model-action.", sorted(valid_actions))

        # Validate --set-state-model
        if getattr(args, "set_state_model", None):
            state, models_str = args.set_state_model
            valid_states = {"idle", "computer", "chatty"}
            if config and config.state_models:
                valid_states.update(config.state_models.keys())
            if state not in valid_states:
                fail(f"Invalid state '{state}' for --set-state-model.", sorted(valid_states))
            # Validate models (comma-separated)
            valid_models = set()
            if config:
                for models in config.state_models.values():
                    valid_models.update(models)
                for path in [config.general_models_path, config.system_models_path, config.chat_models_path]:
                    if os.path.exists(path):
                        valid_models.update([f.replace('.onnx','') for f in os.listdir(path) if f.endswith('.onnx')])
            models = [m.strip() for m in models_str.split(',')]
            invalid = [m for m in models if valid_models and m not in valid_models]
            if invalid:
                fail(f"Invalid model(s) for --set-state-model: {', '.join(invalid)}", sorted(valid_models))

        # Validate --set-listen-for (no strict validation, but could add keys)
        # Validate --set-mode
        if getattr(args, "set_mode", None):
            mode, value = args.set_mode
            valid_modes = {"voice", "text"}
            if config and hasattr(config, "config_data"):
                valid_modes.update(getattr(config.config_data, "modes", {}).keys())
            if mode not in valid_modes:
                fail(f"Invalid mode '{mode}' for --set-mode.", sorted(valid_modes))

    # Validate system subcommands
    if getattr(args, "command", None) == "system":
        if getattr(args, "system_command", None) == "start-on-boot":
            valid_actions = {"enable", "disable", "status"}
            if getattr(args, "boot_action", None) not in valid_actions:
                fail(f"Invalid action '{args.boot_action}' for start-on-boot.", sorted(valid_actions))
        if getattr(args, "system_command", None) == "updates":
            valid_actions = {"check", "enable-auto-check", "disable-auto-check"}
            if getattr(args, "update_action", None) not in valid_actions:
                fail(f"Invalid action '{args.update_action}' for updates.", sorted(valid_actions))
if __name__ == '__main__':
    cli_main()