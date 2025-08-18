import warnings as _w

_w.warn(
    "config.py is deprecated; use chatty_commander.app.config", DeprecationWarning, stacklevel=2
)
from chatty_commander.app.config import *  # noqa
