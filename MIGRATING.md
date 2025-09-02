# Migrating to package paths (src/chatty_commander/\*)

This release begins consolidating code under `src/chatty_commander`. Root-level modules remain as shims for backward compatibility but now emit `DeprecationWarning`. The `command_executor.py` shim has been removed; import from `chatty_commander.app.command_executor` instead.

What changed

- Console entry now points to the package CLI: `chatty_commander.cli.cli:cli_main`.
- A new CLI module lives at `src/chatty_commander/cli/cli.py`.
- Root `cli.py` forwards to the package and re-exports symbols used by tests (cli_main, ConfigCLI, run_app, CommandExecutor, HelpfulArgumentParser).
- Remaining root shims emit `DeprecationWarning`:
  - config.py → chatty_commander.app.config
  - utils/logger.py → chatty_commander.utils.logger

How to update imports

- Before: `from config import Config`
  After: `from chatty_commander.app.config import Config`

- Before: `from command_executor import CommandExecutor`
  After: `from chatty_commander.app.command_executor import CommandExecutor`

- Before: `import utils.logger as logger`
  After: `from chatty_commander.utils import logger`

- Before: entrypoint via root `cli.py`
  After: prefer: `python -m chatty_commander.cli.cli` or installed `chatty-commander`

Timeline

- These shims will remain for at least one minor release. Warnings are enabled so you can update in advance.

## Console entry reality note (2025-08)

- Primary console entry: `chatty_commander.cli.cli:main`
- Backward-compatible alias: `cli_main()` remains available for older references.
