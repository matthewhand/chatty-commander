import sys
import argparse
from config_cli import ConfigCLI
from main import main as run_app

def config_func(args):
    cli = ConfigCLI()
    if args.interactive:
        cli.interactive_mode()
    elif args.model and args.action:
        cli.set_model_action(args.model, args.action)
    else:
        print('For config, use --interactive or provide --model and --action.')
        sys.exit(1)

def cli_main():
    parser = argparse.ArgumentParser(description='ChattyCommander CLI')
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help='Run the ChattyCommander application')
    run_parser.set_defaults(func=run_app)

    # Config subcommand
    config_parser = subparsers.add_parser('config', help='Configure the application')
    config_parser.add_argument('--model', help='Set the model name')
    config_parser.add_argument('--action', help='Set the action for the model')
    config_parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    config_parser.set_defaults(func=config_func)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == '__main__':
    cli_main()