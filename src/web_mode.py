"""Legacy compatibility shim for ``from web_mode import ...`` imports."""
from chatty_commander.compat import expose

expose(globals(), "web_mode")
