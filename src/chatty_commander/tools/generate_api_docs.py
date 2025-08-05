#!/usr/bin/env python3
"""
generate_api_docs facade

This module now delegates to the modularized implementation:
- cli.main handles CLI parsing and exit codes
- workflow.generate_docs performs the docs generation

Backwards compatibility:
- Exposes main() for script entry
- Re-exports workflow.generate_docs for programmatic use
"""

from __future__ import annotations

import sys

from .cli import main as _main


def main() -> int:
    # Preserve original behavior of returning an exit code 0 on success
    return _main(None)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
