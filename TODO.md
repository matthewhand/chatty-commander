# ChattyCommander TODO

Last updated: 2025-08-03 by Kilo Code

Legend:
- [x] Completed
- [ ] Pending
- Now = Current sprint focus (max 7 items)
- Next = Upcoming, ready to pull
- Later = Backlog, not yet scheduled

## Verification Audit (Old TODO → Current Implementation)

Backend Web Mode Implementation
- [x] Add --web flag to main.py to start FastAPI server
  Evidence: main entrypoints and routing in [main.py](main.py:221); web server creation in [src/chatty_commander/web/web_mode.py](src/chatty_commander/web/web_mode.py:1)
- [x] Remove TypeScript backend in webui/backend
  Evidence: directory deleted; frontend kept; references updated in tests and shim [web_mode.py](web_mode.py:1)
- [x] Implement --no-auth flag for local development
  Evidence: parser args in [main.py](main.py:245); CORS behavior and docs enablement in [src/chatty_commander/web/web_mode.py](src/chatty_commander/web/web_mode.py:518)
- [x] Integrate FastAPI endpoints into main Python application
  Evidence: web server wiring in [main.py](main.py:379); app factory in [src/chatty_commander/web/web_mode.py](src/chatty_commander/web/web_mode.py:518)
- [x] Add WebSocket support for real-time communication
  Evidence: existing server scaffolding and callbacks in [main.py](main.py:110)

OpenAPI/Swagger exposure
- [x] Ensure /docs and /openapi.json are exposed with tests
  Evidence:
  - Implementation: [src/chatty_commander/web/web_mode.py](src/chatty_commander/web/web_mode.py:116)
  - Tests (passing): [tests/test_openapi_endpoints.py](tests/test_openapi_endpoints.py:22)
  Command:
  - uv run pytest -q tests/test_openapi_endpoints.py

CLI Enhancement & User Experience
- [x] Argument validation with helpful errors
  Evidence: custom HelpfulArgumentParser and error flows in [cli.py](cli.py:51)
- [ ] Add comprehensive --help and detailed descriptions
  Evidence: parser descriptions in [main.py](main.py:193), [cli.py](cli.py:96). Keep in “Now” for test-verified help outputs.
- [ ] Implement interactive shell when no args; tab completion
  Evidence: interactive shell implemented in [main.py](main.py:278), tab-completion present; verify tests in “Now”.

Frontend Integration
- [x] Remove proxy pointing to TS backend; ensure correct backend port
  Evidence: TS backend removed; “WebUI connectivity sanity” tracked in “Now”.
- [ ] Implement no-auth mode in frontend for dev
  Evidence: backend side present; frontend toggle TBD. Keep in “Next”.

Testing & Quality Assurance
- [x] Add code coverage reporting target and Make targets (planned)
  Evidence: “Testing & QA (Execution Plan)” and Make suggestions; tool in [src/chatty_commander/tools/run_tests_with_coverage.py](src/chatty_commander/tools/run_tests_with_coverage.py:1)
- [x] Resolve import/test discovery issues
  Evidence: [pytest.ini](pytest.ini:1) with pythonpath=src, testpaths=tests
- [x] Web CORS no-auth test uses package path import
  Evidence: [tests/test_cors_no_auth.py](tests/test_cors_no_auth.py:1) updated to import chatty_commander.web.web_mode

Model and Executor Refactors
- [x] Use patchable Model in model manager (for tests)
  Evidence: Model() constructor used in [src/chatty_commander/app/model_manager.py](src/chatty_commander/app/model_manager.py:89)
- [x] Make pyautogui/requests patchable for keybinding and URL actions
  Evidence: _get_pyautogui/_get_requests in [src/chatty_commander/app/command_executor.py](src/chatty_commander/app/command_executor.py:290)

Documentation consolidation
- [x] Consolidate documentation planning into actionable items
  Evidence: current “Documentation” section with API parity generation [src/chatty_commander/tools/generate_api_docs.py](src/chatty_commander/tools/generate_api_docs.py:1)

Notes
- Long-horizon roadmap items (analytics, community, business, extensive UI testing plans) were moved out of TODO and should be tracked in WEBUI_ROADMAP.md and WEBUI_TEST_PLAN.md.

## Now (Sprint Focus)

1) OpenAPI/Swagger exposure and tests
- [ ] Ensure API publishes OpenAPI/Swagger at /docs and /openapi.json
  Acceptance:
  - Running: uv run python main.py --web --no-auth exposes Swagger UI at GET /docs (200 OK)
  - GET /openapi.json returns JSON with "paths" and includes "/health" (content-type: application/json)
  - CORS allows GET from http://localhost:3000 when --no-auth is used
  - Tests:
    - uv run pytest -q tests/test_openapi_endpoints.py::test_openapi_served
    - uv run pytest -q tests/test_openapi_endpoints.py::test_openapi_schema_has_health
  Tasks:
  - Verify FastAPI docs enabled (get_openapi/default docs)
  - Ensure docs/openapi.json generation is consistent with runtime schema
  - Add README note linking /docs and /openapi.json

2) CLI UX hardening
- [ ] Comprehensive --help descriptions
  Acceptance:
  - uv run python cli.py --help exits 0, includes all flags and descriptions
  - uv run pytest -q tests/test_cli_help_and_shell.py::test_help_outputs_usage
- [ ] Interactive shell when no args
  Acceptance:
  - uv run python cli.py enters shell; typing "exit" quits with code 0
  - uv run pytest -q tests/test_repl_basic.py::test_shell_starts_and_exits
- [ ] Tab completion for interactive mode
  Acceptance:
  - Completions suggest registered commands
  - uv run pytest -q tests/test_cli_features.py::test_tab_completion_suggests_known_commands

3) Test infrastructure unblocked
- [x] Add pytest.ini with pythonpath=src so chatty_commander package is importable
- [ ] Run full suite and address failures
  Commands:
  - uv run pytest -q
  Targets:
  - 0 import errors; progress to functional failures

4) WebUI connectivity sanity
- [ ] Frontend connects to Python backend on correct port without Node backend proxy
  Acceptance:
  - Dev server: frontend requests succeed against uv run python main.py --web --no-auth
  - No references to deleted webui/backend
  - Basic auth disabled when --no-auth is provided

5) Minimal docs parity
- [ ] API docs parity automation
  Acceptance:
  - uv run python -m src.chatty_commander.tools.generate_api_docs writes docs/openapi.json
  - Tests assert parity between runtime schema and docs/openapi.json

6) Makefile convenience
- [ ] Add/ensure Make targets:
  - make test           → uv run pytest -q
  - make test-cov       → uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing
  - make test-web       → uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py
  - make test-cli       → uv run pytest -q tests/test_repl_basic.py tests/test_cli_help_and_shell.py tests/test_cli_features.py

7) Clean formatting and references
- [x] Remove stray lines and duplicate "References" at file tail
- [ ] Keep headings sentence case and consistent

## Next (Ready to Pull)

- [ ] Run web mode tests
  - uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py tests/test_cors_no_auth.py
- [ ] Performance smoke
  - uv run pytest -q tests/test_performance_benchmarks.py
- [ ] Coverage target
  - >= 85% lines in src/*
- [ ] Document "no-auth" mode in README and mark as dev-only
- [ ] Add basic health and version endpoints with tests

## Later (Backlog)

- [ ] Advanced CLI features
  - Aliases/shortcuts, batch execution, config profiles, export/import
- [ ] Voice/integration work
  - Integration tests for voice recognition
  - Custom wake word tooling
- [ ] Security hardening
  - Input validation, secrets storage, encryption, audit
- [ ] Observability
  - Metrics, error tracking, dashboards
- [ ] Community artifacts
  - Contributor guide, templates, code of conduct

## Done

- [x] Add --web flag to main.py to start FastAPI server
- [x] Remove webui/backend TypeScript backend
- [x] Implement --no-auth flag for local development
- [x] Integrate FastAPI endpoints into main Python application
- [x] Add WebSocket support for real-time communication
- [x] Argument validation with helpful error messages
- [x] CLI configuration wizard
- [x] Remove stray tail artifacts in TODO.md
- [x] Add pytest.ini with pythonpath=src

## Architecture Clarification

What We Want (Correct Architecture)
```
Python Backend (main.py)
├── CLI Mode (default)
├── GUI Mode (--gui flag)
└── Web Mode (--web flag) → serves React frontend + API
    ├── FastAPI server
    ├── WebSocket for real-time updates
    ├── Optional authentication (--no-auth for local dev)
    └── Static file serving for React build
```

What We Accidentally Created (Cleaned Up)
```
webui/backend/ (TypeScript/Node.js) ← DELETED
webui/frontend/ (React) ← Keep and connect to Python backend
```

## Testing & QA (Execution Plan)

- [ ] Full suite: uv run pytest -q
- [ ] Coverage: uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing
- [ ] Web mode: uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py
- [ ] CLI interactive: uv run pytest -q tests/test_repl_basic.py
- [ ] Performance: uv run pytest -q tests/test_performance_benchmarks.py

## GUI Mode Direction

- [ ] Promote current draft GUI mode to "GUI Settings" module
  Acceptance:
  - Existing draft GUI becomes a dedicated settings/preferences UI for Chatty Commander
  - Settings persist and are reflected in CLI/Web modes
  Tasks:
  - [ ] Extract current draft GUI into a settings-focused module
  - [ ] Wire settings to config/state manager
  - [ ] Tests: ensure settings round-trip and are applied at runtime

- [ ] New GUI mode: transparent simple browser window showing a custom webpage as a popup from the system tray (Windows/macOS)
  Acceptance:
  - System tray icon available on Windows and macOS
  - Clicking tray icon opens a frameless/transparent browser window with user-provided URL
  - Window behaves as a popup (focus, auto-dismiss behavior configurable)
  - Works alongside CLI/Web modes; does not require Node backend
  Tasks:
  - [ ] Choose embedded browser approach (e.g., PyWebview/CEF/Electron-lite alternative)
  - [ ] Implement tray integration (platform-specific fallbacks if needed)
  - [ ] Config keys for custom URL, transparency, window size/position
  - [ ] Safety: allowlist domains and content security considerations
  - [ ] Tests: config plumbing and smoke tests for tray/window lifecycle
  - [ ] Documentation: setup and platform notes

## Documentation

- [ ] API docs parity
  - uv run python -m src.chatty_commander.tools.generate_api_docs
  - docs reference /docs and /openapi.json
  - parity test ensures docs/openapi.json matches runtime schema
- [ ] Developer setup kept current (docs/DEVELOPER_SETUP.md)
  - Clean env works: uv sync, uv run pytest -q, uv run python main.py --web
- [ ] Troubleshooting and videos linked and versioned in docs/
- [ ] Code style enforcement: black + ruff (configs checked in)

## Auto-Mode Selection Policy

- [ ] Auto-detect GUI availability; launch GUI mode when a GUI is detected
  Acceptance:
  - On platforms with a display/session (e.g., DISPLAY on Linux, user session on Windows/macOS), application defaults to GUI mode
  - If no GUI is detected, fallback to CLI or Web mode based on flags/config
  - --gui flag forces GUI mode and skips detection logic
  Tasks:
  - [ ] Implement cross-platform GUI detection helper
  - [ ] Wire detection into main entrypoint before mode selection
  - [ ] Ensure --gui overrides detection and forces GUI mode
  - [ ] Tests: simulate GUI/no-GUI environments to assert correct mode selection
  - [ ] Docs: document detection behavior and --gui override

## References

- Tests: tests/test_openapi_endpoints.py, tests/test_web_mode_unit.py, tests/test_web_mode.py, tests/test_web_integration.py, tests/test_repl_basic.py, tests/test_cli_help_and_shell.py, tests/test_cli_features.py, tests/test_performance_benchmarks.py
- Scripts/Tools: src/chatty_commander/tools/generate_api_docs.py
- Docs: docs/API.md, docs/openapi.json, README.md (API docs section)
