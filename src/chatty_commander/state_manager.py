import warnings as _w

_w.warn(
    "state_manager.py is deprecated; use chatty_commander.app.state_manager",
    DeprecationWarning,
    stacklevel=2,
)
from chatty_commander.app.state_manager import *  # noqa: F401,F403,E402
