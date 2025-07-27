import argparse
import sys
from config_cli import ConfigCLI
from main import main as run_application

def main():
    parser = argparse.ArgumentParser(description='ChattyCommander CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help='Run the ChattyCommander application')

    # Config subcommand
    config_parser = subparsers.add_parser('config', help='Configure the application')
    config_parser.add_argument('--model-action', nargs=2, metavar=('MODEL', 'ACTION'), help='Set a model action non-interactively')

    args = parser.parse_args()

    if args.command == 'run':
        run_application()
    elif args.command == 'config':
        cli = ConfigCLI()
        if args.model_action:
            model, action = args.model_action
            cli.set_model_action(model, action)
        else:
            cli.interactive_mode()

if __name__ == '__main__':
    main()