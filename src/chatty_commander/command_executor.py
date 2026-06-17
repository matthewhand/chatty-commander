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


<<<<<<< HEAD:src/chatty_commander/command_executor.py
def __getattr__(name: str):  # type: ignore[override]
    if name == "CommandExecutor":
        from chatty_commander.app.command_executor import (
            CommandExecutor,  # type: ignore
        )

        return CommandExecutor
    raise AttributeError(name)
=======
def main() -> int:
    """Main operation."""
    if not CFG.exists():
        print("config.json not found", file=sys.stderr)
        return 2
    data = json.loads(CFG.read_text())
    commands = set((data.get("commands") or {}).keys())
    missing: list[str] = []
    for state, names in (data.get("state_models") or {}).items():
        for name in names or []:
            if name not in commands:
                missing.append(f"{state}:{name}")
    if missing:
        print("Config validation: MISSING commands referenced in state_models:")
        for m in sorted(missing):
            print(" -", m)
        return 1
    print("Config validation: OK")
    return 0
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16:src/chatty_commander/tools/validate_config.py


# Make these names visible to patchers; CommandExecutor is provided lazily via __getattr__
__all__ = ["pyautogui", "requests"]
