"""Development-time package shim for src-layout.

This package exists only to make `python -m chatty_commander...` work from the
repo root without an editable install. It extends the package search path to
include the real implementation under `src/chatty_commander` and exposes
basic metadata like ``__version__`` used by tests.
"""

from __future__ import annotations

import os as _os
import pkgutil as _pkgutil

# Extend this package's search path to include the src/ implementation
_here = _os.path.dirname(_os.path.abspath(__file__))
_src_pkg = _os.path.abspath(_os.path.join(_here, "..", "src", "chatty_commander"))

# Ensure this package behaves like a namespace spanning both locations
__path__ = _pkgutil.extend_path(__path__, __name__)  # type: ignore[name-defined]
if _src_pkg not in __path__:
    __path__.append(_src_pkg)  # type: ignore[attr-defined]

# Expose __version__ consistently whether or not the package is installed
try:
    from importlib.metadata import PackageNotFoundError  # type: ignore
    from importlib.metadata import version as _version  # type: ignore

    try:
        __version__ = _version("chatty-commander")
    except PackageNotFoundError:  # pragma: no cover - build-time fallback
        __version__ = "0.0.0+dev"
except Exception:  # pragma: no cover - extremely defensive
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
