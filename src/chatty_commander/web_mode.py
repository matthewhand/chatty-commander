import warnings as _w

"""Compat shim: prefer :mod:`chatty_commander.web.web_mode`"""

_w.warn(
    "web_mode.py is deprecated; use chatty_commander.web.web_mode",
    DeprecationWarning,
    stacklevel=2,
)
from chatty_commander.web.web_mode import *  # noqa

try:
    pass  # re-export for tests
except Exception:
    pass
