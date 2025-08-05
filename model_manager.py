# Compatibility shim for tests that import `model_manager` at repo root.
# Prefer package module when available, else fall back to local src module.
import warnings as _w

_w.warn(
    "model_manager.py is a compatibility shim; preferred import is chatty_commander.app.model_manager",
    DeprecationWarning,
)

try:
    from chatty_commander.app.model_manager import *  # type: ignore  # noqa
except Exception:
    from src.chatty_commander.app.model_manager import *  # type: ignore  # noqa
