# Compatibility shim for tests that import `command_executor` at repo root.
# Ensure src/ on sys.path, expose patch points (pyautogui, requests), and re-export CommandExecutor.
import os as _os
import sys as _sys
import warnings as _w

_w.warn(
    "command_executor.py is a legacy shim; prefer chatty_commander.app.command_executor",
    DeprecationWarning,
    stacklevel=2,
)

# Add the project src root (parent of this package) to sys.path for repo-root execution
_pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
_root_src = _os.path.abspath(_os.path.join(_pkg_dir, ".."))
if _root_src not in _sys.path:
    _sys.path.insert(0, _root_src)

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
