"""Compatibility shim re-exporting :mod:`chatty_commander.main`.

Historically this module loaded a top-level ``main`` using ``importlib`` so
tests could import ``chatty_commander.main`` from the repository root. Now that
``main`` lives inside the package, we simply import it directly and expose the
relevant functions for any lingering imports of :mod:`chatty_commander.main_shim`.
"""

from __future__ import annotations

from chatty_commander import main as _root_main

create_parser = _root_main.create_parser
run_orchestrator_mode = _root_main.run_orchestrator_mode
