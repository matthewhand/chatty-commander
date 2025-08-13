import warnings as _w

_w.warn(
    "default_config.py is deprecated; use chatty_commander.app.default_config",
    DeprecationWarning,
    stacklevel=2,
)
from chatty_commander.app.default_config import *  # noqa
