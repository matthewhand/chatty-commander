#!/usr/bin/env python3
"""
generate_api_docs facade

This module delegates to the modularized implementation in this package:
- cli.main handles CLI argument parsing and exit codes
- workflow.generate_docs performs the docs generation

Backwards compatibility:
- Exposes main() for script entry
- Keeps module name stable for tests importing this path
"""

from __future__ import annotations

import sys

from .cli import main as _main


def main() -> int:
    """Run the docs generator CLI and return its exit code."""
    return _main(None)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
