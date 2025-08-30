"""
Main entry point for ChattyCommander.

This module serves as the primary entry point that delegates to the CLI package.
It provides backward compatibility and ensures the application can be run from
the package root.
"""

from .cli.main import main, create_parser, run_orchestrator_mode

__all__ = ["main", "create_parser", "run_orchestrator_mode"]