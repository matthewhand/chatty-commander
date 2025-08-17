"""Compatibility wrapper for the command-line interface.

This module allows importing ``cli`` for legacy tests by re-exporting the
actual CLI implementation from :mod:`chatty_commander.cli.cli`.
"""

from chatty_commander.cli.cli import *  # noqa: F401,F403
