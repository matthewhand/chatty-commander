"""
Root-level shim to expose Config for tests importing `from config import Config`.

Primary source of truth lives in src/chatty_commander/app/config.py.
We attempt, in order:
  1) import chatty_commander.app.config (when src is on sys.path via pytest.ini)
  2) explicit file-path load from src/chatty_commander/app/config.py
"""
from __future__ import annotations

import importlib.util as _ilu
import os as _os
import sys as _sys
import warnings as _w

_w.warn(
    "config.py is a legacy shim; please import from chatty_commander.app.config in future versions",
    DeprecationWarning,
    stacklevel=2,
)

_repo_root = _os.path.dirname(_os.path.abspath(__file__))
_src_dir = _os.path.join(_repo_root, "src")
if _src_dir not in _sys.path:
    _sys.path.insert(0, _src_dir)

# 1) Try normal import via package path
try:
    from chatty_commander.app.config import *  # type: ignore  # noqa: F401,F403
except Exception:
    # 2) Fallback to explicit file load
    _candidate = _os.path.join(_src_dir, "chatty_commander", "app", "config.py")
    _spec = _ilu.spec_from_file_location("chatty_commander.app.config", _candidate)
    if not _spec or not _spec.loader:
        tried = [
            "import chatty_commander.app.config",
            _candidate,
        ]
        try:
            raise FileNotFoundError(
                "Unable to locate chatty_commander.app.config. Tried:\n - " + "\n - ".join(tried)
            )
        except FileNotFoundError as err:
            raise FileNotFoundError(
                "Unable to locate chatty_commander.app.config. Tried:\n - " + "\n - ".join(tried)
            ) from err
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)  # type: ignore[attr-defined]
    globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("_")})
