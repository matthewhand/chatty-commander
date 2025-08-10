"""Package shim to expose root-level main module under chatty_commander.main.

This allows tests to import chatty_commander.main even when running from repo root.
"""

from __future__ import annotations

import importlib

_root_main = importlib.import_module("main")

create_parser = _root_main.create_parser
run_orchestrator_mode = _root_main.run_orchestrator_mode


