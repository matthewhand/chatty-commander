#!/usr/bin/env python3

import sys
import argparse
import os

# Set DISPLAY environment variable if not set (for GUI applications)
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

from config_cli import ConfigCLI
from main import main as run_app
from config import Config

def config_func(args):
    cli = ConfigCLI()
    if args.interactive:
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
            update_info = config.check_for_updates()
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
    parser = argparse.ArgumentParser(description='ChattyCommander CLI')
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help='Run the ChattyCommander application')
    run_parser.add_argument('--display', type=str, default=None, help='Override DISPLAY environment variable (e.g., :0)')
    run_parser.set_defaults(func=run_app)

    # GUI subcommand
    gui_parser = subparsers.add_parser('gui', help='Launch the desktop GUI application')
    gui_parser.set_defaults(func=lambda args: gui_command())

    # Config subcommand
    config_parser = subparsers.add_parser('config', help='Configure the application')
    config_parser.add_argument('--list', action='store_true', help='List current configuration')
    config_parser.add_argument('--set-model-action', nargs=2, metavar=('MODEL', 'ACTION'), help='Set action for a model')
    config_parser.add_argument('--set-state-model', nargs=2, metavar=('STATE', 'MODELS'), help='Set models for a state (comma-separated)')
    config_parser.add_argument('--set-listen-for', nargs=2, metavar=('KEY', 'VALUE'), help='Set what to listen for')
    config_parser.add_argument('--set-mode', nargs=2, metavar=('MODE', 'VALUE'), help='Set mode options')
    config_parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    config_parser.set_defaults(func=config_func)
    
    # System management subcommands
    system_parser = subparsers.add_parser('system', help='System management commands')
    system_subparsers = system_parser.add_subparsers(dest='system_command', required=True)
    
    # Start on boot commands
    boot_parser = system_subparsers.add_parser('start-on-boot', help='Manage start on boot')
    boot_subparsers = boot_parser.add_subparsers(dest='boot_action', required=True)
    boot_subparsers.add_parser('enable', help='Enable start on boot')
    boot_subparsers.add_parser('disable', help='Disable start on boot')
    boot_subparsers.add_parser('status', help='Check start on boot status')
    
    # Update commands
    update_parser = system_subparsers.add_parser('updates', help='Manage updates')
    update_subparsers = update_parser.add_subparsers(dest='update_action', required=True)
    update_subparsers.add_parser('check', help='Check for updates')
    update_subparsers.add_parser('enable-auto-check', help='Enable automatic update checking')
    update_subparsers.add_parser('disable-auto-check', help='Disable automatic update checking')
    
    system_parser.set_defaults(func=system_func)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
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

if __name__ == '__main__':
    cli_main()