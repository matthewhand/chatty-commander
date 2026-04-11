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

"""Thin wrapper around :mod:`chatty_commander.cli.cli` for backward compatibility."""

from __future__ import annotations

from typing import Any

import chatty_commander.cli.cli as _cli

# Mirror patchable globals so tests that stub attributes on this module continue to work.
Config = _cli.Config
ModelManager = _cli.ModelManager
StateManager = _cli.StateManager
CommandExecutor = _cli.CommandExecutor
setup_logger = _cli.setup_logger
generate_default_config_if_needed = _cli.generate_default_config_if_needed


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
        if name in globals():
            setattr(_cli, name, globals()[name])


def create_parser(*args: Any, **kwargs: Any) -> Any:  # pragma: no cover - thin shim
    return _cli.create_parser(*args, **kwargs)


def run_orchestrator_mode(
    *args: Any, **kwargs: Any
) -> Any:  # pragma: no cover - thin shim
    _propagate_patches()
    return _cli.run_orchestrator_mode(*args, **kwargs)


def main(*args: Any, **kwargs: Any) -> Any:
    """Entry point preserving legacy patch points before delegating to CLI main."""
    _propagate_patches()
    return _cli.cli_main(*args, **kwargs)


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

if __name__ == "__main__":
    import sys
    sys.exit(main())
