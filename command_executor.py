# Compatibility shim for tests that import `command_executor` at repo root.
# Ensure src/ on sys.path, expose patch points (pyautogui, requests), and re-export CommandExecutor.
import os as _os, sys as _sys

_src_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "src")
if _src_path not in _sys.path:
    _sys.path.insert(0, _src_path)

# Expose attributes that tests patch directly on this module
try:
    import pyautogui  # type: ignore
except Exception:
    pyautogui = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

# Re-export implementation
from chatty_commander.app.command_executor import CommandExecutor  # type: ignore

# Make these names visible to patchers
__all__ = ["CommandExecutor", "pyautogui", "requests"]
