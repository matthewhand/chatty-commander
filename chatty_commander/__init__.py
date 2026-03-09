# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
__path__ = _pkgutil.extend_path(__path__, __name__)
if _src_pkg not in __path__:
    __path__.append(_src_pkg)

# Expose __version__ consistently whether or not the package is installed
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _version

    try:
        __version__ = _version("chatty-commander")
    except PackageNotFoundError:  # pragma: no cover - build-time fallback
        __version__ = "0.0.0+dev"
except Exception:  # pragma: no cover - extremely defensive
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
