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

"""
Tools used by AdvisorsService.

``TOOL_REGISTRY`` maps each advisor tool name to the module (within this
package) that defines its openai-agents ``FunctionTool`` instance. Use
:func:`get_tool_instance` to resolve an instance lazily; it returns ``None``
when the openai-agents SDK (or the tool's optional dependencies) are not
available, mirroring how providers guard their tool imports.
"""

from __future__ import annotations

import importlib
from typing import Any

# tool name -> (module within this package, attribute holding the FunctionTool)
TOOL_REGISTRY: dict[str, tuple[str, str]] = {
    "browser_analyst": ("browser_analyst", "browser_analyst_tool_instance"),
    "dograh_place_call": ("dograh_call", "dograh_call_tool_instance"),
    "switch_mode": ("switch_mode", "switch_mode_tool_instance"),
}


def get_tool_instance(name: str) -> Any | None:
    """Return the FunctionTool instance registered under ``name``.

    Returns ``None`` for unknown names, when the tool module cannot be
    imported, or when the instance is unavailable (e.g. the openai-agents
    SDK is not installed).
    """
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        return None
    module_name, attr = entry
    try:
        module = importlib.import_module(f".{module_name}", __name__)
    except ImportError:
        return None
    return getattr(module, attr, None)


__all__ = ["TOOL_REGISTRY", "get_tool_instance"]
