"""Compat shim: prefer :mod:`chatty_commander.web.web_mode`"""
from .compat import expose

expose(globals(), "web_mode")
