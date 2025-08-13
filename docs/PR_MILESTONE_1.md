# PR: Packaging cleanup + Package CLI + Deprecation shims + CI polish

## Summary
- Fix packaging and console entry by introducing a package CLI and keeping a root shim.
- Add DeprecationWarnings to legacy shims (config.py, command_executor.py, utils/logger.py).
- Clean test/coverage config and improve CI quality (ruff/black + coverage, uv).

## Changes
- Packaging / CLI
  - New package CLI: `src/chatty_commander/cli/cli.py` with fully-featured commands (run, gui, config, list, exec, system, interactive shell with basic tab completion).
  - Root `cli.py` is now a thin shim, re-exporting symbols used in tests and emitting a DeprecationWarning.
  - Console script: `chatty_commander.cli.cli:cli_main`.
- Deprecations
  - Root shims now warn: `config.py`, `command_executor.py`, `utils/logger.py`.
- Coverage config
  - Omit `config-*.py` to avoid warnings from stray temporary files.
- CI & Tooling
  - Rewrote CI to a single job that runs uv, ruff, black --check, and pytest with coverage, and optionally uploads to Codecov.
  - Added a `.pre-commit-config.yaml` with ruff, black, and prettier for docs.
- Docs
  - Quickstart in README.md (uv setup, test, CLI, web).
  - Added MIGRATING.md with import path guidance and timeline.

## Rationale
- Make `src/` authoritative and reduce duplicate tooling.
- Keep backward compatibility via shims while guiding consumers to update imports.
- Improve CI signal quality and dev ergonomics.

## Testing
- Full suite with coverage:
  - `pytest -q --cov=. --cov-report=term --cov-report=html`
  - Result: All tests pass; coverage HTML written to `htmlcov/`.

## Backward compatibility
- All legacy entry points remain with deprecation warnings and re-exported names to support existing tests/patches.

## Out of scope
- Major refactors to `main.py` and deep advisor features; these stay unchanged.

## Follow-ups (tracked in MIGRATING.md/TODO)
- Continue migrating imports in internal modules from root shims to package paths.
- Consider optional dependencies grouping for web/gui/wakeword.
- Move `main.py` logic under `src/chatty_commander/main.py` and keep a root shim.

