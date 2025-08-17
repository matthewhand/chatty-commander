"""Compatibility shim for config_cli module."""

# Compatibility shim to preserve `from config_cli import ConfigCLI`
from chatty_commander.config_cli import *  # noqa: F401,F403
