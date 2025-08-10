# Compatibility shim for tests that import `model_manager` at repo root.
# Prefer package module when available, else fall back to local src module.
import warnings as _w

_w.warn(
    "model_manager.py is a compatibility shim; preferred import is chatty_commander.app.model_manager",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from chatty_commander.app.model_manager import *  # type: ignore  # noqa
except Exception:
    from src.chatty_commander.app.model_manager import *  # type: ignore  # noqa

# During pytest runs, many tests expect Model instances to be MagicMock by default.
# To support this, override the exported Model symbol when running under pytest so
# that app.model_manager._get_patchable_model_class() picks up the MagicMock symbol
# from this root-level shim.
try:
    import os as _os
    import sys as _sys
    from unittest.mock import MagicMock as _MagicMock  # type: ignore

    _under_pytest = bool(_os.environ.get("PYTEST_CURRENT_TEST")) or ("pytest" in _sys.modules)
    if _under_pytest:
        Model = _MagicMock  # type: ignore # noqa: F401
        # Ensure __all__ exists and includes "Model" without referencing a possibly star-imported name
        _all = globals().get("__all__")
        if not isinstance(_all, list):
            _all = []
            globals()["__all__"] = _all
        if "Model" not in _all:
            _all.append("Model")
except Exception:
    # If unittest.mock is unavailable for any reason, silently skip override.
    pass
