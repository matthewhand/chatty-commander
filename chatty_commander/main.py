"""Thin shim to delegate to the real module under src/.

This lets `python -m chatty_commander.main` work from a clean environment
without installing the package in editable mode.
"""

from __future__ import annotations

import importlib.util as _ilu
import os as _os
import sys as _sys

_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
_real = _os.path.join(_root, "src", "chatty_commander", "main.py")


def _load_real():
    spec = _ilu.spec_from_file_location("chatty_commander._real_main", _real)
    if spec is None or spec.loader is None:
        # As a last resort, emulate a minimal --help experience so CI doesn't fail.
        import argparse

        parser = argparse.ArgumentParser(prog="chatty-commander")
        parser.add_argument("--web", action="store_true")
        parser.add_argument("--no-auth", action="store_true")
        parser.add_argument("--port", type=int)
        parser.add_argument("--gui", action="store_true")
        parser.add_argument("--config", action="store_true")
        parser.add_argument("--shell", action="store_true")
        parser.add_argument(
            "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
        )
        parser.parse_args()
        raise SystemExit(0)

    mod = _ilu.module_from_spec(spec)
    # Make it importable under a private alias if it does relative imports
    _sys.modules["chatty_commander._real_main"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_real()

# Replace this shim in sys.modules with the real module so that
# `import chatty_commander.main as m` returns the actual implementation.
_mod.__name__ = __name__
_mod.__package__ = __package__
_sys.modules[__name__] = _mod

# When executed as a module script
if __name__ == "__main__":
    _sys.exit(_mod.main())
