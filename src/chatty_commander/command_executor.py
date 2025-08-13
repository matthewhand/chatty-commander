"""Compat shim: prefer :mod:`chatty_commander.app.command_executor`"""
from .compat import load

try:  # pragma: no cover - best effort import
    import pyautogui  # type: ignore
except Exception:  # noqa: BLE001 - optional dependency
    pyautogui = None  # type: ignore

try:  # pragma: no cover
    import requests  # type: ignore
except Exception:  # noqa: BLE001
    requests = None  # type: ignore

__all__ = ["pyautogui", "requests"]


def __getattr__(name: str):
    if name == "CommandExecutor":
        module = load("command_executor")
        return getattr(module, name)
    raise AttributeError(name)
