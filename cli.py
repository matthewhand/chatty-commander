#!/usr/bin/env python3
# Legacy CLI shim; forwards to package CLI. Prefer `python -m chatty_commander.cli.cli`.
import warnings as _w

_w.warn(
    "cli.py is a legacy shim; prefer chatty_commander.cli.cli",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export expected symbols so tests can patch via 'cli.*'
from chatty_commander.cli.cli import (  # noqa: E402
    cli_main,
    ConfigCLI,  # type: ignore
    run_app,    # type: ignore
    CommandExecutor,  # type: ignore
    HelpfulArgumentParser,  # type: ignore
)

if __name__ == "__main__":
    cli_main()
