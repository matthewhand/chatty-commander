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

# utils/logger.py shim
# Re-export the real logger module so tests can import and monkeypatch via 'utils.logger'
import sys as _sys
import warnings as _w
from importlib import import_module as _import_module

_w.warn(
    "utils/logger.py is a legacy shim; prefer chatty_commander.utils.logger",
    DeprecationWarning,
    stacklevel=2,
)

_real = _import_module("chatty_commander.utils.logger")

# Re-export public names
setup_logger = _real.setup_logger
report_error = _real.report_error

# Re-export all other names dynamically
for _name in dir(_real):
    if _name.startswith("_"):
        continue
    if _name not in globals():
        globals()[_name] = getattr(_real, _name)

# Ensure the module object identity is shared for patching
_sys.modules.setdefault("utils", _sys.modules.get("utils", type(_sys)("utils")))
_sys.modules["utils.logger"] = _sys.modules[__name__]
