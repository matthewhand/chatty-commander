"""Legacy compatibility shim for ``from config import ...`` imports.

New code should import from :mod:`chatty_commander.app.config` instead.
"""

from chatty_commander.compat import expose

expose(globals(), "config")
