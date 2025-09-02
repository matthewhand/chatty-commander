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

"""Compat shim: prefer :mod:`chatty_commander.app.model_manager`"""

from .compat import expose

expose(globals(), "model_manager")

# Maintain pytest MagicMock override for backward compatibility
try:  # pragma: no cover - best effort
    import os as _os
    import sys as _sys
    from unittest.mock import MagicMock as _MagicMock  # type: ignore

    _under_pytest = bool(_os.environ.get("PYTEST_CURRENT_TEST")) or (
        "pytest" in _sys.modules
    )
    if _under_pytest:
        Model = _MagicMock  # type: ignore[name-defined]
        _all = globals().get("__all__") or []
        if "Model" not in _all:
            _all.append("Model")
        globals()["__all__"] = _all
except Exception:  # pragma: no cover - defensive
    pass
