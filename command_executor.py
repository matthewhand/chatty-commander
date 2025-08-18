import warnings as _w

_w.warn(
    "command_executor.py is deprecated; use chatty_commander.app.command_executor",
    DeprecationWarning,
    stacklevel=2,
)
from chatty_commander.app.command_executor import *  # noqa
