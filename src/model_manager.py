"""Legacy compatibility shim for ``from model_manager import ...`` imports."""
from chatty_commander.compat import expose

expose(globals(), "model_manager")
