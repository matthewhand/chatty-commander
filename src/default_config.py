"""Compatibility shim for default_config module."""

# Compatibility shim to preserve `from default_config import ...`
from chatty_commander.default_config import *  # noqa: F401,F403
