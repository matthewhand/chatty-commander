# ChattyCommander TODO

Last updated: 2025-08-13 by OpenAI Assistant

Legend:
- [x] Completed
- [ ] Pending
- Now = Current sprint focus (max 7 items)
- Next = Upcoming, ready to pull
- Later = Backlog, not yet scheduled

## Background Docker Task Runner & Summaries

Goal: allow users to queue `--yolo -p` prompts that spawn Dockerized Codex tasks, surface rolling 3-word summaries, and expose a kill button.

### Tasks
- [ ] **Scheduler & Queue** – launch container jobs with prompt, model selection (`gpt-oss:20b` default), and persistent metadata.
- [ ] **Log Tail & Summarizer** – buffer last _N_ lines, invoke LLM to output enforced 3-word summaries at intervals.
- [ ] **UI Badge & Stop Control** – display rotating summaries and a square-in-circle stop button that terminates the container.
- [ ] **Cleanup & History** – remove summaries when jobs finish; optional persistence of logs and summaries.

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

## Design summary: OpenAI-Agents advisor

- **Core SDK**: `openai-agents` (local), derived from OpenAI Swarm; supports MCP, handoff, and as_tool with BYO-LLM.
- **LLM mode**: Default to `completion` API for broad compatibility (e.g., GPT-OSS20B and other local/uncensored models). The upstream default `responses` API has limited third-party support.
- **Platforms**: Modular adapters for Discord, Slack, and other messengers.
- **Advisors**: Per-app/system prompts (e.g., philosophy-focused) with tab-aware context switching that preserves identity across apps.
- **Avatar (optional)**: 3D anime-style avatar with lip-sync via TalkingHead.
- **Browser/analyst**: Built-in analyst/browser capabilities.
- **Goal**: Personal AI advisors with a modular multi-platform UI and LLM backend; suitable for hackathon/contest entry.

## Feature: OpenAI-Agents advisor (Work Plan)

### Milestone A — MVP foundations

- [x] SDK integration
  - Wire `openai-agents` as a service module; enable MCP, handoff, and `as_tool`
  - Config gate: `advisors.enabled`
  - Acceptance:
    - Refactored providers.py to use `openai_agents.Agent` instead of `openai.OpenAI`
    - Updated service.py to orchestrate agent-based providers
    - Confirmed existing tests pass by mocking `Agent.chat()` method
    - Migrated dependency from `openai>=1.48.0` to `openai-agents>=0.1.0`
    - Preserved compatibility shims for `CompletionProvider` and `ResponsesProvider`
    - Added comprehensive docstrings explaining new agent-oriented architecture
    - Feature can be toggled on/off via config

- [ ] LLM API mode & providers
  - Default to `completion`; optional `responses` via `advisors.llm_api_mode`
  - BYO-LLM provider wiring (OpenAI-compatible base URL + key; local models e.g., GPT-OSS20B)
  - Config keys: `advisors.model`, `advisors.provider.base_url`, `advisors.provider.api_key`
  - Acceptance:
    - Unit tests cover selection logic and completion vs responses
    - E2E test prompts a local provider and returns text

- [ ] Tools: MCP, handoff, and as_tool
  - Define tool interface; register `browser_analyst` as first tool
  - Acceptance:
    - Tool invocation path exercises MCP/tool-call and returns a structured result
    - Handoff between advisors can be triggered and logged

- [ ] Node.js bridge API (Discord/Slack external adapters)
  - Define HTTP/WebSocket contract between Node bridge and Python advisor core
  - Acceptance:
    - Contract documented in `docs/OPENAI_AGENTS_ADVISOR.md` (endpoints, payloads, auth)
    - Local mock verifies end-to-end message flow through the bridge

- [x] Web API entrypoint for advisors
  - POST /api/v1/advisors/message accepts platform/channel/user/text
  - Acceptance:
    - Unit test posts message and receives echo with advisor header

- [x] Bridge endpoint auth and echo
  - POST /bridge/event requires `X-Bridge-Token`; returns advisor echo reply
  - Acceptance:
    - Unit tests cover 401 without token and 200 with token

- [x] Orchestrator skeleton
  - Unifies text/gui/web/cv/wakeword/discord flags and dispatch
  - Acceptance:
    - Unit tests verify adapter selection and text dispatch to command sink

- [x] Advisor context memory (per platform/channel/user)
  - In-memory store with get/clear endpoints
  - Acceptance:
    - Unit tests cover memory add/get/clear and API endpoints

- [x] Provider selection (completion vs responses)
  - Build provider stub and wire into advisor replies; tests cover both modes
  - Acceptance:
    - Unit tests assert provider type and hint presence in replies

- [ ] Prompt templating
  - Build prompt envelope helper and integrate persona prompt
  - Acceptance:
    - Unit test validates envelope; advisor path composes prompt deterministically

- [ ] Recurring prompts (MVP)
  - Add `RecurringPrompt` dataclass and renderer; docs + tests
  - Acceptance:
    - JSON example parses; variables render; docs linked in docs/README.md

- [ ] Advisor memory persistence (opt-in)
  - JSONL append-only persistence with env/config toggles
  - Acceptance:
    - Unit test writes two lines; config flag toggles persistence

- [ ] Context manager (tab/app-aware)
  - Map app/tab identity → persona/system prompt → memory store
  - Persistence layer for identities and conversation state
  - Acceptance:
    - Switching app contexts changes system prompt and preserves per-app memory

- [ ] Browser/analyst tool (basic)
  - Safe HTTP fetch + readability extraction + summarize
  - Safety: domain allowlist and timeouts
  - Acceptance:
    - Deterministic test on a snapshot page yields expected summary structure

- [ ] Docs (quickstart)
  - `docs/OPENAI_AGENTS_ADVISOR.md` quickstart updated with config keys and run steps
  - Example configs for Discord/Slack

### Milestone B — Enhancements & polish

- [ ] Optional 3D avatar (TalkingHead) behind config flag; lip-sync to advisor output
- [ ] Persona library (e.g., philosophy-focused) and quick switching UX
- [ ] Provider prompt templates per persona/model
- [ ] Observability: basic metrics, structured logs for tool calls and handoffs
- [ ] Security: secret management guidance, allowlists, model safety toggles
- [ ] Platform polish: richer Discord/Slack features (threads, edits, attachments)

### Milestone C — Test matrix & CI

- [ ] E2E flows for Discord and Slack using recorded sessions/mocks
- [ ] Coverage ≥ 85% for advisor modules; per-platform adapters have smoke tests
- [ ] CI secrets strategy documented; integration tests gated for local/dev only

## Completed ✅

All major "Now" items have been delivered:
- ✅ OpenAPI/Swagger exposure and tests
- ✅ CLI UX hardening (comprehensive help, examples)
- ✅ Test infrastructure (90% coverage gate, green CI)
- ✅ WebUI connectivity sanity (docs + tests)
- ✅ API docs parity automation (Makefile + CI)
- ✅ Makefile convenience targets
- ✅ Health/version/metrics endpoints with tests
- ✅ PyInstaller packaging + CI artifacts + smoke tests
- ✅ Standalone install documentation
- ✅ E2E workflows and smoke script

## Now (Sprint Focus)

1) OpenAPI/Swagger exposure and tests
- [x] Ensure API publishes OpenAPI/Swagger at /docs and /openapi.json
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
- [x] Comprehensive --help descriptions
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
- [x] Run full suite and address failures
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
- [x] API docs parity automation
  Acceptance:
  - uv run python -m src.chatty_commander.tools.generate_api_docs writes docs/openapi.json
  - Tests assert parity between runtime schema and docs/openapi.json

6) Makefile convenience
- [x] Add/ensure Make targets:
  - make test           → uv run pytest -q
  - make test-cov       → uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing
  - make test-web       → uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py
  - make test-cli       → uv run pytest -q tests/test_repl_basic.py tests/test_cli_help_and_shell.py tests/test_cli_features.py

7) Clean formatting and references
- [x] Remove stray lines and duplicate "References" at file tail
- [ ] Keep headings sentence case and consistent

8) Cross-platform launch (Windows/macOS)
- [x] Windows: add PowerShell launcher and instructions (uv install, `uv run python main.py --web --no-auth`)
  Acceptance:
  - `./scripts/windows/start-web.ps1` launches server; docs include prerequisites and path notes
- [x] macOS: add launch instructions and shell script
  Acceptance:
  - `./scripts/macos/start-web.sh` launches server; docs list Gatekeeper notes and `uv` setup
- [x] README/docs updates with OS-specific quickstart
  Acceptance:
  - `README.md` and `docs/README.md` show Windows/macOS launch snippets

9) Node.js bridge API implementation (external app for Discord/Slack)
- [x] Create external Node.js application that connects to Python advisor API
  Acceptance:
  - Node.js app can authenticate with Python bridge endpoint using shared secret
  - Discord/Slack webhooks can send messages to Node.js app
  - Node.js app forwards messages to Python advisor API and returns responses
  - Messages are routed back to appropriate Discord/Slack channels
  Tasks:
  - [x] Design Node.js app architecture (Express.js server, Discord.js/Slack SDK)
  - [x] Implement authentication with Python bridge endpoint
  - [x] Add Discord bot integration with slash commands and message handling
  - [x] Add Slack app integration with event subscriptions and message handling
  - [x] Implement message routing between platforms and Python advisor
  - [x] Add error handling and logging for cross-platform communication
  - [x] Create deployment documentation for Node.js bridge

10) Real LLM provider integrations
- [x] Implement actual LLM API calls in CompletionProvider and ResponsesProvider
  Acceptance:
  - CompletionProvider makes real API calls to OpenAI-compatible endpoints
  - ResponsesProvider implements streaming responses for real-time chat
  - Both providers handle authentication, rate limiting, and error recovery
  - Support for local models like GPT-OSS20B via custom base URLs
  Tasks:
  - [x] Add OpenAI SDK integration with configurable base URLs
  - [x] Implement streaming responses for real-time advisor interactions
  - [x] Add retry logic and exponential backoff for API failures
  - [x] Support for custom model parameters (temperature, max_tokens, etc.)
  - [x] Add provider health checks and connection testing
  - [x] Implement fallback providers for high availability

11) Production deployment infrastructure
- [x] Docker containerization with multi-stage builds
  Acceptance:
  - Dockerfile builds successfully with Python 3.11-slim base
  - Image includes all dependencies and runs tests
  - Non-root user for security, health checks included
  Tasks:
  - [x] Create multi-stage Dockerfile with builder and production stages
  - [x] Add docker-compose.yml for local development
  - [x] Include optional Redis and PostgreSQL services
  - [x] Add volume mounts for data persistence
  - [x] Implement health checks and resource limits

12) Kubernetes production deployment
- [x] Complete Kubernetes manifests for production scaling
  Acceptance:
  - Deployment, Service, Ingress, ConfigMap, Secret manifests
  - Persistent volume claims for data and logs
  - Health checks, resource limits, security best practices
  Tasks:
  - [x] Create comprehensive Kubernetes manifests
  - [x] Add ConfigMap for configuration management
  - [x] Implement Secret for API keys and sensitive data
  - [x] Add persistent volume claims for data storage
  - [x] Include ingress configuration with TLS support
  - [x] Add automated deployment script with health checks

13) Advanced voice processing integration
- [ ] Integrate OpenWakeWord for voice wake word detection
  Acceptance:
  - Voice wake word triggers advisor interactions
  - Works with CLI mode and advisor system
  - Configurable wake word sensitivity and recognition
  Tasks:
  - [ ] Add OpenWakeWord dependency and configuration
  - [ ] Implement wake word detection in CLI mode
  - [ ] Connect wake word to advisor service
  - [ ] Add voice command processing pipeline
  - [ ] Test with different wake words and environments
  - [ ] Add voice activity detection and noise filtering

14) Computer vision commands
- [ ] Implement visual command recognition system
  Acceptance:
  - Camera input can trigger system commands
  - Visual gestures recognized and mapped to actions
  - Works alongside voice and text input modes
  Tasks:
  - [ ] Add OpenCV dependency for computer vision
  - [ ] Implement gesture recognition algorithms
  - [ ] Create visual command mapping system
  - [ ] Add camera input handling and processing
  - [ ] Test with different lighting conditions
  - [ ] Add visual feedback and status indicators

15) 3D avatar integration (TalkingHead)
- [ ] Integrate 3D anime-style avatar with lip-sync
  Acceptance:
  - Optional 3D avatar displays during advisor interactions
  - Lip-sync matches generated speech output
  - Configurable avatar appearance and animations
  Tasks:
  - [ ] Research TalkingHead software integration
  - [ ] Add avatar rendering and animation system
  - [ ] Implement lip-sync with speech synthesis
  - [ ] Create avatar configuration options
  - [ ] Add performance optimization for real-time rendering
  - [ ] Test on different hardware configurations

## Next (Ready to Pull)

- [x] Run web mode tests
  - uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py tests/test_cors_no_auth.py
- [ ] Performance smoke
  - uv run pytest -q tests/test_performance_benchmarks.py
- [ ] Coverage target
  - >= 85% lines in src/*
- [ ] Document "no-auth" mode in README and mark as dev-only
- [x] Add basic health and version endpoints with tests

### OpenAI-Agents advisor (MVP)
- [ ] Integrate `openai-agents` SDK (local); enable MCP, handoff, and `as_tool` usage
- [ ] Default model API to `completion` mode; config flag to switch to `responses` if needed
- [ ] BYO-LLM wiring for local models (e.g., GPT-OSS20B); add model selection config
- [ ] Node.js bridge API for Discord/Slack integration (external adapters)
- [ ] Tab-aware context switching with per-app/system prompts and persistent identity
- [ ] Built-in browser/analyst tool available to advisors
- [ ] Docs: add design summary and quickstart for advisor setup

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

### OpenAI-Agents advisor (Enhancements)
- [ ] Optional 3D anime-style avatar via TalkingHead with lip-sync; runtime toggle
- [ ] Multi-platform polish: richer Discord/Slack features and presence
- [ ] Local model optimization: prompt templates for uncensored models; safety/policy toggles
- [ ] UX: advisor persona library (e.g., philosophy-focused) and easy switching

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

## Project Cleanup Roadmap (added by Rovo Dev)

Overview
- Make src/ the single source of truth; keep root-level shims temporarily.
- Fix console entry point and packaging inconsistencies.
- Consolidate logging and document migration.

Phased Plan

1) Packaging and CLI entry
- Update pyproject entry point to a working target:
  - chatty-commander = "cli:cli_main" (temporary)
- Create package CLI (preferred longer term):
  - Create src/chatty_commander/cli/cli.py that exposes cli_main().
  - Then set: chatty-commander = "chatty_commander.cli.cli:cli_main".
  - Keep root cli.py as a shim forwarding to the package entry.
- Remove argparse dependency from project dependencies (stdlib).
- Add DeprecationWarning to shims: config.py, command_executor.py, utils/logger.py.

2) Logger consolidation
- Keep src/chatty_commander/utils/logger.py as real implementation.
- Keep utils/logger.py as shim but warn on import.

3) Normalize imports & docs
- Add uniform deprecation notes to all root shims with removal timeline.
- Add MIGRATING.md mapping old imports to new package paths.

4) CLI consolidation
- Move real CLI to src/chatty_commander/cli/cli.py; make root cli.py a shim.
- Ensure tests that import cli keep working via shim.

5) Main module consolidation
- Move real logic to src/chatty_commander/main.py and make root main.py a shim.
- Keep current shim in src/chatty_commander/main.py during transition.

6) Optional dependencies
- Split extras for web/gui/wakeword in pyproject.

7) CI & tooling
- Add pre-commit config; run ruff/black/pytest in CI.

8) Remove legacy files
- After deprecation window, remove root shims and point all imports to the package.

Milestone 1 (implement now)
- pyproject: Fix console entry to cli:cli_main (done)
- pyproject: Drop argparse dependency (done)
- Add DeprecationWarnings to root shims (done)
- Append this plan to TODO.md under a new section

## Packaging & Distribution (next)

- [x] Implement PyInstaller-based CLI executable build for Linux/macOS/Windows
- [x] Add Makefile targets: build-exe, build-exe-all, dist-clean
- [x] Add CI matrix job to build and upload artifacts on release tags
- [x] Add smoke tests for artifacts (chatty --help, chatty list)
- [x] Document standalone install in README and developer docs

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

## Milestone: Avatar Integration (Completed)
- [x] Integrate TalkingHead 3D avatar as a transparent desktop window.
  - Acceptance Criteria:
    - `uv run python -m src.chatty_commander.main --gui` launches the avatar window.
    - Window is frameless, transparent, and stays on top (best-effort; falls back gracefully).
    - Loads `src/chatty_commander/webui/avatar/index.html` (replace with TalkingHead build output if needed).
    - Tests: avatar launcher unit tests with high coverage (>=90%).
    - Docs: module docstring explains design goals and usage.
    - Headless-safe: GUI path is skipped or returns a non-crashing code when DISPLAY is not available.

## Milestone: Avatar Expressive States & Agent Handoff (In Progress)
- Goal: The avatar should reflect LLM/agent lifecycle states and tool usage with distinct animations and support swapping avatars on agent handoff via openai-agents.

- States and animations (server -> UI mapping):
  - idle: neutral breathing/idle animation
  - thinking: triggered when LLM emits <thinking>...</thinking> content; subtle "thinking" animation
  - processing: general background processing, light activity animation
  - tool_calling: "hacking" animation during tool/function calls (e.g., as_tool/MCP invocations)
  - responding: speaking/response animation
  - error: error/glitch animation
  - handoff: transition animation when handing off to another agent; then swap avatar theme

- Backend tasks:
  - [ ] Extend thinking_state manager with new states: tool_calling, handoff, responding, error
  - [ ] Define unified AgentStateInfo schema: {agent_id, persona_id, state, detail, ts}
  - [ ] Instrument AdvisorsService to:
    - set thinking when entering LLM <thinking>
    - set processing before generate
    - set responding after generate
    - set error on exception
  - [ ] Wrap tool invocation points to broadcast tool_calling start/stop
    - If using openai-agents as_tool or MCP tools, emit start/end (with tool name)
  - [ ] Add openai-agents integration hooks:
    - emit handoff start (from_agent -> to_agent with reasons)
    - emit handoff complete (new agent persona_id/model)
  - [ ] Enhance avatar_ws WebSocket protocol:
    - message types: agent_states_snapshot, agent_state_changed, tool_call_start, tool_call_end, handoff_start, handoff_complete
    - include minimal payloads for UI routing and telemetry
  - [ ] Tests: unit tests for thinking_state transitions, AdvisorsService instrumentation, WS broadcast manager (mock websocket)

- Frontend/UI tasks (TalkingHead):
  - [ ] Implement animation presets for: idle, thinking, processing, tool_calling ("hacking"), responding, error, handoff
  - [ ] Map incoming WS messages to animation state machine
  - [ ] Support avatar theme swap on handoff (agent persona -> avatar skin)
  - [ ] Local dev toggle to simulate states for design work

- Agent persona and avatar theming:
  - [ ] Define persona->avatar_theme registry (JSON) with default and overrides
  - [ ] Backend includes persona_id and optional avatar_theme in WS messages
  - [ ] UI loads theme assets dynamically (preload and graceful fallback)

- Acceptance Criteria:
  - When tools are executed, the avatar plays the "hacking" animation for the duration of the call
  - When LLM emits <thinking>...</thinking>, the avatar shows the "thinking" animation until content switches to normal output
  - On openai-agents handoff, the UI displays a transition animation and swaps to the new agent's avatar theme
  - Unit tests cover state transitions and WS broadcasting; e2e smoke test verifies UI consumes messages correctly
  - Documentation updated with state/event protocol and theming guide

- Documentation:
  - [ ] docs/AVATAR_GUI.md: protocol spec, state machine, theming, dev workflow
  - [ ] README: brief overview and link to AVATAR_GUI.md

### Settings GUI/WebUI for Animation Configuration
- Goal: Allow users to enable/disable animations and map states/categories to specific animations discovered on disk.
- Backend/API
  - [ ] Add endpoint GET /avatar/animations to list available animations by scanning a configured directory (e.g., src/chatty_commander/webui/avatar/animations/ or build assets).
  - [ ] Include metadata: { name, file, category, duration?, loop?, preview? } where feasible.
  - [ ] Config schema: config.gui.avatar with keys: animations_dir, enabled, defaults, state_map: {state->animation}, category_map.
  - [ ] Persist user selections to config and reload at runtime.
  - [ ] Tests: endpoint scanning, config roundtrip, permission checks.
- WebUI/GUI
  - [ ] Settings page to show available animations (from endpoint), toggles, and state mapping controls.

## Milestone: Agent Blueprint Management & Team Orchestration

### Goal
Implement natural language agent blueprint definition with GUI/WebUI integration for comprehensive persona management, team visualization, and dynamic agent lifecycle management.

### Core Features

#### Natural Language Agent Blueprint Definition
- [ ] Create agent blueprint schema that accepts natural language descriptions
  - Acceptance:
    - Schema supports: name, description, persona_prompt, capabilities, team_role, handoff_triggers
    - Natural language parser extracts structured data from free-form descriptions
    - Blueprint validation ensures required fields and capability compatibility
  - Tasks:
    - [ ] Define AgentBlueprint dataclass with comprehensive schema
    - [ ] Implement natural language parser using LLM to extract structured blueprint data
    - [ ] Add blueprint validation and capability checking
    - [ ] Create blueprint serialization/deserialization (JSON/YAML)
    - [ ] Tests: parser accuracy, validation edge cases, serialization roundtrip

#### GUI/WebUI Agent Management Interface
- [ ] Implement comprehensive agent management UI in settings
  - Acceptance:
    - Settings page shows all configured agents with personas, prompts, and team relationships
    - "+Create Agent" button opens natural language blueprint creation dialog
    - "Destroy Agent" option with confirmation dialog before deletion
    - Team visualization shows agent relationships and handoff flows
    - Real-time agent status (active, idle, error) with connection to thinking_state manager
  - Tasks:
    - [ ] Create agent management settings page/component
    - [ ] Implement "+Create Agent" dialog with natural language input field
    - [ ] Add "Destroy Agent" functionality with confirmation modal
    - [ ] Build team visualization component (graph/tree view of agent relationships)
    - [ ] Integrate with existing avatar WebSocket for real-time agent status
    - [ ] Add agent editing capabilities (modify persona, prompts, capabilities)
    - [ ] Tests: UI component tests, agent CRUD operations, team visualization rendering

#### Backend API for Agent Management
- [ ] Extend advisor API with agent blueprint management endpoints
  - Acceptance:
    - POST /api/v1/agents/blueprints - create agent from natural language description
    - GET /api/v1/agents/blueprints - list all configured agents with metadata
    - PUT /api/v1/agents/blueprints/{agent_id} - update agent configuration
    - DELETE /api/v1/agents/blueprints/{agent_id} - remove agent with safety checks
    - GET /api/v1/agents/team - get team structure and relationships
    - POST /api/v1/agents/team/handoff - trigger manual agent handoff
  - Tasks:
    - [ ] Create agent blueprint management router
    - [ ] Implement CRUD operations for agent blueprints
    - [ ] Add team structure API endpoints
    - [ ] Integrate with openai-agents for dynamic agent creation/destruction
    - [ ] Add safety checks for agent deletion (active conversations, dependencies)
    - [ ] Tests: API endpoint coverage, error handling, safety validations

#### Agent Team Orchestration
- [ ] Implement dynamic agent team management with openai-agents integration
  - Acceptance:
    - Agents can be dynamically created/destroyed at runtime
    - Team handoff flows respect blueprint-defined triggers and capabilities
    - Agent personas are properly mapped to avatar themes
    - Team state is persisted and restored across application restarts
  - Tasks:
    - [ ] Integrate agent blueprint system with openai-agents SDK
    - [ ] Implement dynamic agent registration/deregistration
    - [ ] Create team handoff orchestration logic
    - [ ] Add agent-to-avatar theme mapping system
    - [ ] Implement team state persistence (JSON/database)
    - [ ] Add team health monitoring and error recovery
    - [ ] Tests: dynamic agent lifecycle, handoff flows, persistence, error scenarios

#### Animation Setup UI Integration
- [ ] Create dedicated animation configuration interface
  - Acceptance:
    - Separate view/pane/mode for animation setup and testing
    - Preview animations with real-time playback
    - Map animations to agent states and personas
    - Test animation transitions and timing
    - Export/import animation configurations
  - Tasks:
    - [ ] Create animation setup UI component/page
    - [ ] Implement animation preview with playback controls
    - [ ] Add drag-and-drop animation assignment to states
    - [ ] Create animation testing mode with state simulation
    - [ ] Add animation configuration export/import
    - [ ] Integrate with existing /avatar/animations endpoint
    - [ ] Tests: animation UI components, preview functionality, configuration persistence

### Integration Points
- [ ] Connect agent management to existing avatar WebSocket system
- [ ] Integrate with thinking_state manager for real-time agent status
- [ ] Link to openai-agents SDK for actual agent orchestration
- [ ] Connect to avatar theme system for persona-based visual representation
- [ ] Integrate with existing configuration system for persistence

### Documentation
- [ ] Create docs/AGENT_BLUEPRINT_MANAGEMENT.md with:
  - Natural language blueprint syntax and examples
  - GUI/WebUI usage guide for agent management
  - Team orchestration concepts and best practices
  - Animation setup and configuration guide
  - API reference for agent management endpoints

### Acceptance Criteria
- Users can describe agents in natural language and have them automatically configured
- GUI provides intuitive agent creation with "+Create Agent" button
- Agent destruction requires confirmation and handles dependencies safely
- Team visualization shows agent relationships and current status
- Animation setup provides dedicated interface for configuration and testing
- All agent management operations are reflected in real-time across UI components
- System handles agent lifecycle gracefully with proper error recovery
  - [ ] Live preview controls and safe fallbacks when an animation is missing or broken.
  - [ ] Import/export of animation presets.
- Acceptance
  - Users can view animations discovered on disk, toggle them, and assign per-state mappings.
  - Settings persist and are respected by the avatar UI and server broadcasts.

### Intelligent Animation Selection (LLM-based)
- Goal: Dynamically choose an animation based on the content of the model’s thinking/reply.
- Backend service
  - [ ] Add AnimationSelector service that classifies text into a constrained set of labels (e.g., excited, calm, curious, warning, success, error, neutral) using a local LLM (e.g., gpt-oss:20b) or configured provider.
  - [ ] Use regex-constrained output or JSON schema to guarantee one label from the allowed set.
  - [ ] Input sources: (a) accumulated <thinking> buffer snapshots, (b) final assistant reply; configurable thresholds and debounce.
  - [ ] API: POST /avatar/animation/choose { text, context?, candidate_labels? } -> { label, confidence, rationale? }.
  - [ ] WS: emit animation_hint messages so the UI can smoothly transition.
  - [ ] Performance/safety: timeouts, rate-limiting, and disable switch in config.
- UI behavior
  - [ ] Map classified labels to animations via configurable label->animation map; allow overrides.
  - [ ] Fall back to state-based default if classifier returns none or low confidence.
- Tests/metrics
  - [ ] Unit tests for label constraints and fallback logic.
  - [ ] Offline evaluation harness with a small labeled dataset for smoke-quality metrics.
- Acceptance
  - Given representative thinking/reply text, the system selects appropriate animations (e.g., hacking for tool_calling, calm for neutral, warning for errors) and falls back predictably.
