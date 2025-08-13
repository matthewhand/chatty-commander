"""Compat shim: prefer :mod:`chatty_commander.app.config`"""
from .compat import expose

expose(globals(), "config")
