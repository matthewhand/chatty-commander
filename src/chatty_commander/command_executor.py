"""Compat shim: prefer :mod:`chatty_commander.app.command_executor`"""

from typing import TYPE_CHECKING

from .compat import load

if TYPE_CHECKING:  # pragma: no cover
    from .app.command_executor import CommandExecutor

try:  # pragma: no cover - best effort import
    import pyautogui  # type: ignore
except Exception:
    pyautogui = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

__all__ = ["pyautogui", "requests"]


def __getattr__(name: str):  # type: ignore[override]
    if name == "CommandExecutor":
        from chatty_commander.app.command_executor import CommandExecutor  # type: ignore

        return CommandExecutor
    raise AttributeError(name)


# Make these names visible to patchers; CommandExecutor is provided lazily via __getattr__
__all__ = ["pyautogui", "requests"]
