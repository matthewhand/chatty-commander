import os
import sys

# Ensure package root is importable when frozen
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    pkg_root = os.path.abspath(os.path.join(base_dir))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

from chatty_commander.cli.cli import cli_main

if __name__ == "__main__":
    cli_main()
