"""Legacy compatibility shim for ``from command_executor import CommandExecutor``.

Exposes ``pyautogui`` and ``requests`` symbols for tests to patch before the
real implementation is imported.
"""
from chatty_commander.compat import load

try:  # pragma: no cover - best effort import
    import pyautogui  # type: ignore
except Exception:  # noqa: BLE001 - optional dependency
    pyautogui = None  # type: ignore

try:  # pragma: no cover - best effort import
    import requests  # type: ignore
except Exception:  # noqa: BLE001
    requests = None  # type: ignore

__all__ = ["pyautogui", "requests"]


def __getattr__(name: str):  # PEP 562
    if name == "CommandExecutor":
        module = load("command_executor")
        return getattr(module, name)
    raise AttributeError(name)
