# Changelog

## \[Unreleased\] - 2026-06-02

Hardening, bug-fix, and feature-completion rounds (PRs #572–#588), grouped by area.

### CLI

- `--log-level {DEBUG,INFO,WARNING,ERROR}` is now actually applied to the logger (previously parsed and ignored).
- `CHATCOMM_LOG_LEVEL` env var is now applied in web mode.
- `exec <command> --timeout <seconds>` flag added and enforced (command runs in a worker thread, aborts with exit 1 on overrun).
- `python -m chatty_commander.cli.main list` and `exec ...` now work (previously fell through to model-loading and hung); they delegate to the same implementation as the `chatty-commander` console script.
- Interactive-shell `models` command fixed (previously raised `TypeError`).
- `voice test` subcommand is now reachable (handler existed but was never dispatched).
- `list --json` correctly classifies dict-form actions (keypress/url/shell) instead of reporting "unknown".

### Configuration

- `config.json` is now written **atomically** (temp file + `os.replace`) so a crash mid-write can't corrupt it; same for `fs_ops` `write_json`/`write_text`.
- `set_start_on_boot` no longer silently no-ops; it logs that OS-level autostart isn't implemented yet (the preference is still persisted).
- `Config.from_dict()` now sets `.config` and `system_models_path`/`chat_models_path` (previously missing, so a `ModelManager` built from a dict config couldn't find them).
- `reload_config()` now refreshes all derived attributes (model paths, `state_models`, `api_endpoints`, `wakeword_state_map`, `state_transitions`), not just a couple.

### Web API

- Agent blueprint store (`agents.json`) is now lock-guarded and written atomically (concurrent create/update/delete can't corrupt it).
- `GET /api/v1/advisors/personas` now reads personas from configuration (the hardcoded dev seed Jarvis/Friday/HAL was removed).
- `POST /avatar/animation/choose` uses the LLM for classification when available, falling back to keyword hints.
- `GET /api/system/info` no longer returns duplicate environment-variable entries.
- Advisors memory endpoints validate `limit` (1–100) and reject empty platform/channel/user.
- The server no longer runs `npm install`/`npm run build` at startup (frontend must be pre-built); the broken SPA 404 fallback was fixed; the bridge endpoint got `hasattr` and missing-token guards.
- Rate-limit middleware now bounds its in-memory map under rotating-IP bursts.

### Advisors

- Memory load/save failures are now logged (were silently swallowed).
- Invalid platform now raises a clear error listing valid platforms.
- On LLM failure, an intent/sentiment-aware fallback message is returned (still marked `[LLM Error]`).
- Lightweight user-preference learning is recorded each turn and feeds future-turn context.
- Conversation context is saved atomically.
- Intent detection now works for capitalized questions ("What is AI?").
- `current_mode` is now read correctly from config (was always defaulting).

### LLM

- OpenAI availability probe is cached (no live API call on every check).
- LLM JSON extraction is non-greedy; confidence parsing tolerates null/non-numeric values; fallback-backend errors are logged.

### Voice

- Whisper API and voice self-test temp WAV files are now cleaned up (were leaking).
- Command matching uses word boundaries (no more "play" matching "replay"/"display").
- VAD attribute init is guarded; voice-only no-match gives honest feedback.

### Web UI (frontend)

- Commands list "Edit" button now opens the authoring page **pre-filled** for editing.
- A failed command delete now surfaces an error and keeps the dialog open (was silently closing and implying success).
- JSON import validates each command's shape before overwriting config.
- ThemeProvider/authService logging cleaned up; WebSocket frame guards added; `useAuth` retry timeout cleared on unmount.

### Tools / Observability / Avatar / Tests

- `fs_ops` writes are atomic; `create_metrics_router` return type corrected to `APIRouter | None`.
- `with_thinking_state` decorator preserves wrapped-function metadata; avatar audio queue exposes an `AUDIO_PLAYBACK_SUPPORTED=False` flag (playback is simulated, no real audio output).
- Transcription init tests mock whisper/openai so they no longer skip.

## \[0.1.1\] - 2025-08-20

## \[0.1.2\] - 2025-08-21

### Added

- Lite CLI binary build (PyInstaller) and CI release workflow to publish amd64/arm64 artifacts on tags.
- CodeQL scanning and Dependabot updates.

### Fixed/Docs

- OpenAPI docs parity with runtime schema (added /api/v1/version).
- Documentation for action-style commands and tolerant mode.

### Fixed

- Command executor: support both legacy and action-style schemas; tolerant mode returns False for invalid/missing commands in coverage tests; URL actions use timeout when action-style; improved keypress error handling; avoid duplicate critical logs.
- WebSocket avatar route: avoid un-awaited coroutine warning by using `asyncio.run` when no loop is present.

### Tests

- Added focused coverage tests; ensured Python suite passes via `make test`.
- JS tests: allow running on Node \<22 via `tsx` loader; added ESM `shared/ascii.mjs` and updated unit test import.

## \[0.2.0\] - 2024-12-19

### Added

- **E2E Testing**: Comprehensive end-to-end test suite with 90% coverage gate
- **Observability**: Metrics middleware with JSON and Prometheus endpoints (`/metrics/json`, `/metrics/prom`)
- **API Endpoints**:
  - `GET /api/v1/version` - Application version and git SHA
  - `GET /api/v1/health` - Health check with uptime
  - `GET /api/v1/metrics` - Legacy metrics endpoint
- **Agents API**: Full CRUD for agent blueprints with team orchestration
- **Avatar System**: WebSocket-based avatar state broadcasting with animation selection
- **CLI Improvements**: Rich help text with examples, dry-run mode, interactive shell
- **Packaging**: PyInstaller spec with CI artifacts for Linux/macOS/Windows
- **Documentation**:
  - WebUI connectivity guide
  - Standalone install instructions
  - Example workflows and E2E smoke script

### Enhanced

- **Frontend**: React components with WebSocket provider and protected routes
- **Backend**: FastAPI with modular routers, middleware, and comprehensive error handling
- **CI/CD**: Coverage enforcement, frontend testing, artifact builds on tags
- **Developer Experience**: Makefile targets, lint/format automation, comprehensive docs

### Technical

- Thread-safe metrics registry with Counter/Gauge/Histogram/Timer
- RequestMetricsMiddleware for automatic HTTP request instrumentation
- Thinking state manager with async broadcast support
- Isolated test stores for deterministic agent testing
- OpenAPI schema parity validation

## \[0.1.0\] - Initial Release

- Basic CLI and web mode functionality
- Configuration management
- Core command execution framework
