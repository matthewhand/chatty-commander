# Compatibility shim for tests that import `command_executor` at repo root.
# Ensure src/ on sys.path, expose patch points (pyautogui, requests), and lazily expose CommandExecutor.
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

__all__ = ["pyautogui", "requests"]


def __getattr__(name: str):  # type: ignore[override]
    if name == "CommandExecutor":
        from chatty_commander.app.command_executor import CommandExecutor  # type: ignore

        return CommandExecutor
    raise AttributeError(name)


# Make these names visible to patchers; CommandExecutor is provided lazily via __getattr__
__all__ = ["pyautogui", "requests"]
