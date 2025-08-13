"""Compatibility helpers for legacy module paths.

This module provides a central alias table that maps old module names to their
new locations under :mod:`chatty_commander`.  Importers should rely on
:func:`load` or :func:`expose` rather than accessing modules directly.
"""
from __future__ import annotations

import importlib
import warnings
from types import ModuleType
from typing import Dict, Iterable

# Map legacy module names to their modern implementation paths.
ALIASES: Dict[str, str] = {
    "config": "chatty_commander.app.config",
    "model_manager": "chatty_commander.app.model_manager",
    "web_mode": "chatty_commander.web.web_mode",
}


def load(name: str) -> ModuleType:
    """Import and return the modern module for a legacy name.

    A :class:`DeprecationWarning` is emitted each time this function resolves a
    legacy module name.  The warning points developers toward the modern path.
    """
    target = ALIASES[name]
    warnings.warn(
        f"chatty_commander.{name} is deprecated; use {target}",
        DeprecationWarning,
        stacklevel=3,
    )
    return importlib.import_module(target)


def expose(namespace: dict, name: str) -> ModuleType:
    """Populate ``namespace`` with public symbols from the aliased module.

    This mirrors the behaviour of ``from module import *`` while routing through
    the alias table.  ``__all__`` is populated with the exported names from the
    target module (or all non-private names if ``__all__`` is absent).
    """
    module = load(name)
    public: Iterable[str]
    public = getattr(module, "__all__", None) or [n for n in dir(module) if not n.startswith("_")]
    for attr in public:
        namespace[attr] = getattr(module, attr)
    namespace["__all__"] = list(public)
    return module

__all__ = ["ALIASES", "load", "expose"]
