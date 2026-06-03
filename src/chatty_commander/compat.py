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

"""Compatibility helpers for legacy module paths.

Centralise the alias table so the various compatibility shims across the code
base can pull in the modern implementations from a single place.  This avoids
hand-maintaining nearly identical wrappers for each legacy module.
"""

from __future__ import annotations

import importlib
import warnings
from collections.abc import Iterable
from types import ModuleType
from typing import Any

# Map legacy module names to their modern implementation paths.
ALIASES: dict[str, str] = {
    "config": "chatty_commander.app.config",
    "model_manager": "chatty_commander.app.model_manager",
    "web_mode": "chatty_commander.web.web_mode",
    "state_manager": "chatty_commander.app.state_manager",
    "config_cli": "chatty_commander.cli.config",
    "cli": "chatty_commander.cli.cli",
    "default_config": "chatty_commander.app.default_config",
    "wakeword": "chatty_commander.voice.wakeword",
    "command_executor": "chatty_commander.app.command_executor",
    "logger": "chatty_commander.utils.logger",
    "gui": "chatty_commander.gui",
    "avatar_gui": "chatty_commander.avatars.avatar_gui",
    "thinking_state": "chatty_commander.avatars.thinking_state",
    "llm_manager": "chatty_commander.llm.manager",
    "voice_pipeline": "chatty_commander.voice.pipeline",
    "orchestrator": "chatty_commander.app.orchestrator",
    "cli_main": "chatty_commander.cli.main",
    "pyqt5_avatar": "chatty_commander.gui.pyqt5_avatar",
    "tray_popup": "chatty_commander.gui.tray_popup",
}


def load(name: str) -> ModuleType:
    """Import and return the module for ``name`` honouring the alias table."""
    target = ALIASES.get(name, name)
    if target != name:
        warnings.warn(
            f"chatty_commander.{name} is deprecated; use {target}",
            DeprecationWarning,
            stacklevel=3,
        )
    return importlib.import_module(target)


def expose(namespace: dict[str, Any], name: str) -> ModuleType:
    """Populate ``namespace`` with the public symbols from the target module."""
    module = load(name)
    public: Iterable[str]
    public = getattr(module, "__all__", None) or [
        attr for attr in dir(module) if not attr.startswith("_")
    ]
    for attr in public:
        namespace[attr] = getattr(module, attr)
    namespace["__all__"] = list(public)
    return module


__all__ = ["ALIASES", "load", "expose"]
