# utils/logger.py shim
# Re-export the real logger module so tests can import and monkeypatch via 'utils.logger'
import sys as _sys
import warnings as _w
from importlib import import_module as _import_module

_w.warn(
    "utils/logger.py is a legacy shim; prefer chatty_commander.utils.logger",
    DeprecationWarning,
    stacklevel=2,
)

_real = _import_module("chatty_commander.utils.logger")

# Re-export public names
setup_logger = _real.setup_logger
report_error = _real.report_error

# Re-export all other names dynamically
for _name in dir(_real):
    if _name.startswith("_"):
        continue
    if _name not in globals():
        globals()[_name] = getattr(_real, _name)

# Ensure the module object identity is shared for patching
_sys.modules.setdefault("utils", _sys.modules.get("utils", type(_sys)("utils")))
_sys.modules["utils.logger"] = _sys.modules[__name__]
