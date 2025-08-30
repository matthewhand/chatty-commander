"""
Package entry point for ChattyCommander.

This allows the package to be executed with: python -m chatty_commander
"""

from .cli.main import main

if __name__ == "__main__":
    main()