# ChattyCommander TODO

Last updated: 2025-08-03 by Kilo Code

Legend:
- [x] Completed
- [ ] Pending
- Now = Current sprint focus (max 7 items)
- Next = Upcoming, ready to pull
- Later = Backlog, not yet scheduled

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

## Documentation

- [ ] API docs parity
  - uv run python -m src.chatty_commander.tools.generate_api_docs
  - docs reference /docs and /openapi.json
  - parity test ensures docs/openapi.json matches runtime schema
- [ ] Developer setup kept current (docs/DEVELOPER_SETUP.md)
  - Clean env works: uv sync, uv run pytest -q, uv run python main.py --web
- [ ] Troubleshooting and videos linked and versioned in docs/
- [ ] Code style enforcement: black + ruff (configs checked in)

## References

- Tests: tests/test_openapi_endpoints.py, tests/test_web_mode_unit.py, tests/test_web_mode.py, tests/test_web_integration.py, tests/test_repl_basic.py, tests/test_cli_help_and_shell.py, tests/test_cli_features.py, tests/test_performance_benchmarks.py
- Scripts/Tools: src/chatty_commander/tools/generate_api_docs.py
- Docs: docs/API.md, docs/openapi.json, README.md (API docs section)
