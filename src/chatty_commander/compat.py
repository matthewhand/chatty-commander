from __future__ import annotations

import importlib

# Map legacy module names to their modern implementation paths.
ALIASES: dict[str, str] = {
    "config": "chatty_commander.app.config",
    "model_manager": "chatty_commander.app.model_manager",
    "web_mode": "chatty_commander.web.web_mode",
}


def expose(name: str):
    """Return imported module for a legacy short-name (or pass through)."""
    target = ALIASES.get(name, name)
    return importlib.import_module(target)
