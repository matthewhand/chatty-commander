"""Legacy shim for configuration.

Prefer importing from ``chatty_commander.app.config``.
"""

from __future__ import annotations

try:
    from .app.config import *  # type: ignore  # noqa: F401,F403
except Exception as err:
    raise ImportError(
        "chatty_commander.config is a shim; failed to import chatty_commander.app.config"
    ) from err

__all__ = [name for name in globals() if not name.startswith("_")]
