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

"""Compat shim: prefer :mod:`chatty_commander.app.command_executor`"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    pass

try:  # pragma: no cover - best effort import
    import pyautogui  # type: ignore
except Exception:
    pyautogui = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

__all__ = ["pyautogui", "requests"]


def __getattr__(name: str):  # type: ignore[override]
    if name == "CommandExecutor":
        from chatty_commander.app.command_executor import (
            CommandExecutor,  # type: ignore
        )

        return CommandExecutor
    raise AttributeError(name)


# Make these names visible to patchers; CommandExecutor is provided lazily via __getattr__
__all__ = ["pyautogui", "requests"]
