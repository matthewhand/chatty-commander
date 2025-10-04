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

"""Thin wrapper around :mod:`chatty_commander.cli.main` for backward compatibility."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_cli_main = import_module("chatty_commander.cli.main")

# Mirror patchable globals so tests that stub attributes on this module continue to work.
Config = _cli_main.Config
ModelManager = _cli_main.ModelManager
StateManager = _cli_main.StateManager
CommandExecutor = _cli_main.CommandExecutor
setup_logger = _cli_main.setup_logger
generate_default_config_if_needed = _cli_main.generate_default_config_if_needed


def _propagate_patches() -> None:
    """Copy any locally patched globals onto the real CLI module."""
    for name in (
        "Config",
        "ModelManager",
        "StateManager",
        "CommandExecutor",
        "setup_logger",
        "generate_default_config_if_needed",
    ):
        setattr(_cli_main, name, globals()[name])


def create_parser(*args: Any, **kwargs: Any) -> Any:  # pragma: no cover - thin shim
    return _cli_main.create_parser(*args, **kwargs)


def run_orchestrator_mode(
    *args: Any, **kwargs: Any
) -> Any:  # pragma: no cover - thin shim
    _propagate_patches()
    return _cli_main.run_orchestrator_mode(*args, **kwargs)


def main(*args: Any, **kwargs: Any) -> Any:
    """Entry point preserving legacy patch points before delegating to CLI main."""
    _propagate_patches()
    return _cli_main.main(*args, **kwargs)


__all__ = [
    "main",
    "create_parser",
    "run_orchestrator_mode",
    "Config",
    "ModelManager",
    "StateManager",
    "CommandExecutor",
    "setup_logger",
    "generate_default_config_if_needed",
]
