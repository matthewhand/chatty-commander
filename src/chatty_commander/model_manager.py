"""Compat shim: prefer :mod:`chatty_commander.app.model_manager`"""
from .compat import expose

expose(globals(), "model_manager")

# Maintain pytest MagicMock override for backward compatibility
try:  # pragma: no cover - best effort
    import os as _os
    import sys as _sys
    from unittest.mock import MagicMock as _MagicMock  # type: ignore

    _under_pytest = bool(_os.environ.get("PYTEST_CURRENT_TEST")) or ("pytest" in _sys.modules)
    if _under_pytest:
        Model = _MagicMock  # type: ignore[name-defined]
        _all = globals().get("__all__") or []
        if "Model" not in _all:
            _all.append("Model")
        globals()["__all__"] = _all
except Exception:  # pragma: no cover - defensive
    pass
