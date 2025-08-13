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

__all__ = ["pyautogui", "requests", "CommandExecutor"]


<<<<<<< HEAD

# Lazily load CommandExecutor to avoid circular import during app module init
def __getattr__(name: str):  # PEP 562
    if name == "CommandExecutor":
        import importlib

        m = importlib.import_module("chatty_commander.app.command_executor")
        return getattr(m, name)
=======
def __getattr__(name: str):  # PEP 562
    if name == "CommandExecutor":
        module = load("command_executor")
        return getattr(module, name)
>>>>>>> 231e8853a6a87e434f7239c3dc0540d12f1f1a94
    raise AttributeError(name)
