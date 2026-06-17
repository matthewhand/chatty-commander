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

"""Compatibility shim exposing the CLI configuration helpers."""

from __future__ import annotations

from typing import Any

<<<<<<< HEAD:src/chatty_commander/config_cli.py
from chatty_commander.cli.config import ConfigCLI


def handle_config_cli(args: Any) -> int:
    """Entry point kept for callers expecting the legacy function."""
    _ = args  # Legacy signature; no arguments are currently consumed.
    ConfigCLI().run_wizard()
    return 0


__all__ = ["ConfigCLI", "handle_config_cli"]
=======

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a JSON file with pretty formatting."""
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_text(path: Path, data: str) -> None:
    """Write a text file."""
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write(data)
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16:src/chatty_commander/tools/fs_ops.py
