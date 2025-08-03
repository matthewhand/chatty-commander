import warnings as _w; _w.warn("web_mode.py is deprecated; use chatty_commander.web.web_mode", DeprecationWarning); from chatty_commander.web.web_mode import *  # noqa

try:
    from chatty_commander.web.web_mode import create_app  # re-export for tests
except Exception:
    pass
