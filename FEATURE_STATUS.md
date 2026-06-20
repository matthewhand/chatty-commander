# Feature Status — audited 2026-06-10

This document is a mechanically verifiable feature audit of ChattyCommander.
Every row was re-verified against the working tree on **2026-06-10** (post-reset
baseline `3ac5ea05` plus the security/wiring fixes through `cc52b876`). It is a
**snapshot, not a contract**:

- **Re-verify before acting on any row.** Line numbers drift as code changes
  (several files were being edited concurrently while this audit ran). Each
  evidence cell names the symbol as well as the line so rows can be re-found
  with `grep -n` even after drift.
- Status legend: ✅ working (verified by reading the code and/or passing tests)
  · 🟡 partial (exists but with a specific named gap) · 🔲 unstarted (only a
  placeholder exists) · ❌ broken (present but does not do what it claims).
- No aspirational rows: if it is not in the tree today, it is not listed as ✅.

Test baseline at audit time: 883 tests collected, full suite reported green
(859 run); a 208-test smoke subset covering the rows below was re-run during
this audit (`uv run pytest ... -q --no-cov` — all passed, see "How to
regenerate").

## Summary

| Domain | ✅ | 🟡 | 🔲 | ❌ | Rows |
|---|---|---|---|---|---|
| Voice | 2 | 4 | 0 | 1 | 7 |
| Command execution | 3 | 1 | 0 | 0 | 4 |
| Web backend | 8 | 0 | 0 | 0 | 8 |
| Web UI | 4 | 0 | 0 | 0 | 4 |
| CLI | 4 | 2 | 0 | 0 | 6 |
| Advisors / LLM | 6 | 0 | 0 | 0 | 6 |
| Integrations | 2 | 1 | 1 | 0 | 4 |
| Desktop GUI / Avatar | 2 | 2 | 1 | 0 | 5 |
| Observability | 3 | 0 | 0 | 0 | 3 |
| Infra / CI | 4 | 2 | 0 | 1 | 7 |
| **Total** | **38** | **12** | **2** | **2** | **54** |

## Voice

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Wake-word detection module (openwakeword ONNX) | ✅ | `src/chatty_commander/voice/wakeword.py:51` `WakeWordDetector` with `MockWakeWordDetector` fallback; `openwakeword>=0.4.0` is a declared dependency (`pyproject.toml:33`); tests: `tests/test_wakeword_comprehensive.py`, `tests/test_voice.py` (passed in smoke run) |
| Transcription module (Whisper local/API + mock) | 🟡 | `src/chatty_commander/voice/transcription.py:56` `TranscriptionBackend` ABC, `:207` `VoiceTranscriber`; tests `tests/test_transcription_comprehensive.py` pass — **gap: `whisper` is not in `pyproject.toml` dependencies or extras (only a mypy override at `pyproject.toml:222`), so a default install silently falls back to the mock transcriber** |
| Text-to-speech module (pyttsx3 + mock) | 🟡 | `src/chatty_commander/voice/tts.py:94` `TextToSpeech`, `:81` `MockTTSBackend`; tests `tests/test_tts_comprehensive.py` pass — **gap: `pyttsx3` is not a declared dependency (only mypy override `pyproject.toml:229`); real speech requires a manual install** |
| End-to-end `VoicePipeline` (wake → record → transcribe → respond) | 🟡 | `src/chatty_commander/voice/pipeline.py:48` `VoicePipeline` implemented and tested (`tests/test_voice.py::TestVoicePipeline`) — **gap: only consumed by the self-test harness `voice/cli.py` and tests; not wired into the default `chatty-commander` run loop** |
| Real voice listening in default CLI mode | ❌ | `src/chatty_commander/cli/cli.py:74` calls `model_manager.listen_for_commands()`, which is a **simulation**: `src/chatty_commander/app/model_manager.py:199-204` (`async_listen_for_commands`) sleeps 0.1 s then returns `random.choice(active_models)` 5 % of the time — no audio inference happens in default mode |
| Wake-word adapter in orchestrator mode | ✅ | `src/chatty_commander/app/orchestrator.py:136` `OpenWakeWordAdapter` uses the real `WakeWordDetector` when voice deps import (falls back to mock/dummy otherwise); enabled via `--orchestrate --enable-openwakeword` (`cli/cli.py` `run_orchestrator_mode`); tests `tests/test_main_orchestrator.py` (passed in smoke run) |
| Web voice control endpoints | 🟡 | `src/chatty_commander/web/routes/voice.py:55-67` `/api/voice/start` and `/api/voice/stop` — **gap: they only flip an in-memory `state["running"]` bool; no voice pipeline is started or stopped** |

## Command execution

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Keypress / URL / shell actions | ✅ | `src/chatty_commander/app/command_executor.py:113-135` dispatches `keypress`/`url`/`shell`/`custom_message`/`voice_chat`/`dograh_call`; tests `tests/test_command_executor.py` + `tests/command_executor/` (passed in smoke run) |
| `dograh_call` action (wake word → phone call) | ✅ | `src/chatty_commander/app/command_executor.py:329` `_execute_dograh_call`; error-reason strings pinned by tests (commit `0ce4e9a9`); `tests/test_command_executor.py` passed in smoke run |
| State machine (idle / chatty / computer) | ✅ | `src/chatty_commander/app/state_manager.py` `StateManager` transitions + callbacks; `tests/test_state_manager.py` passed in smoke run (the toggle-mode failures listed in the pre-reset audit no longer reproduce) |
| State-driven ONNX model loading | 🟡 | `src/chatty_commander/app/model_manager.py:40` imports `wakewords.model.Model`, **a package that is not in `pyproject.toml` dependencies — default installs fall back to the stub `Model` class at `:45-47` that only stores the path**; `.onnx` directory scanning exists (`load_model_set`), but combined with the simulated listener (see Voice) no real model inference runs in default mode |

## Web backend

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Auth middleware on **both** app factories | ✅ | `src/chatty_commander/web/server.py:201` and `src/chatty_commander/web/web_mode.py:567` both add `AuthMiddleware` (the P0 "create_app missing auth" bug was fixed in `0ec4feb4`); production guard `ensure_no_auth_allowed` at `server.py:123` refuses `no_auth=True` under `CHATTY_ENV=production`; `tests/test_auth.py` passed in smoke run |
| Single source of truth for routers | ✅ | `src/chatty_commander/web/server.py:147` `register_shared_routers` used by both `server.create_app` and `web_mode.WebModeServer._create_app` (`web_mode.py` imports it; commit `696283cb`) — the audit-era factory divergence is resolved |
| Core REST API (status, config, state, commands) | ✅ | `src/chatty_commander/web/routes/core.py`; `tests/test_core_routes.py`, `tests/test_web_server.py` (70 tests, suite green) |
| WebSocket realtime channel | ✅ | `src/chatty_commander/web/routes/ws.py:58` `@router.websocket("/ws")`; covered by `tests/test_web_server.py` / `tests/test_web_api_isolated.py` (suite green) |
| Audio device endpoints | ✅ | `src/chatty_commander/web/routes/audio.py:94-100` GET `/api(/v1)/audio/devices` (real pyaudio enumeration with `available=False` graceful degradation) and POST `/api(/v1)/audio/device` (landed in `d1b496a2`); `tests/test_audio_routes.py` passed in smoke run |
| Preferences + theme endpoints | ✅ | `src/chatty_commander/web/routes/preferences.py:99` GET/PUT `/api/preferences`; `src/chatty_commander/web/routes/themes.py:86` GET `/api/themes`, GET/POST `/api/theme` (landed in `2f4c12c8`); `tests/test_preferences_routes.py`, `tests/test_theme_routes.py` passed in smoke run |
| Dograh status/workflow routes | ✅ | `src/chatty_commander/web/routes/dograh.py` with graceful degradation when the client is unavailable; `tests/test_web_routes_dograh.py` passed in smoke run |
| Agents API (blueprint CRUD, team, handoff) | ✅ | `src/chatty_commander/web/routes/agents.py:91-97` file-backed store (`~/.chatty_commander/agents.json`, `RLock`-serialized), endpoints from `:207`; `tests/test_agents_api.py` (suite green) |

## Web UI

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Six SPA pages (Login, Dashboard, Configuration, Commands, CommandAuthoring, VoiceTest) | ✅ | `webui/frontend/src/pages/{LoginPage,DashboardPage,ConfigurationPage,CommandsPage,CommandAuthoringPage,VoiceTestPage}.tsx`; routed in `webui/frontend/src/App.tsx`; `npm run build` green at audit time |
| Auth-protected routing + WebSocket provider | ✅ | `webui/frontend/src/components/ProtectedRoute.tsx` (+ `ProtectedRoute.test.tsx`, `ProtectedRoute.auth.test.tsx`), `WebSocketProvider.tsx` (+ unit/error tests) |
| Resilience + session UX (ErrorBoundary, SessionExpiredModal, persisted theme) | ✅ | `webui/frontend/src/components/{ErrorBoundary,SessionExpiredModal,ThemeProvider}.tsx` (each with `*.test.tsx`); ThemeProvider persists the selected DaisyUI theme to `localStorage` key `chatty.theme` |
| Dograh status card on dashboard | ✅ | `webui/frontend/src/components/DograhStatusCard.tsx` backed by the verified `/api/v1/dograh/*` routes above |
| Audio device picker | ✅ | `webui/frontend/src/pages/ConfigurationPage.tsx:78` fetches `/api/v1/audio/devices` and `:85` posts `/api/v1/audio/device` — both served by `routes/audio.py:94-100` (this frontend/backend mismatch from the audit is fixed) |

## CLI

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Entry point + run modes (`--web`, `--gui`, `--config`) | ✅ | `pyproject.toml:73` `chatty-commander = "chatty_commander.cli.cli:cli_main"`; `src/chatty_commander/cli/cli.py:53` `run_cli_mode`, `:135` `run_web_mode`, `:232` `run_gui_mode`; `tests/test_cli_features.py` (suite green) |
| `dograh` subcommand group | ✅ | Registered once through the main parser: `src/chatty_commander/cli/cli.py:376` `register_dograh_subparser(subparsers)`, dispatched at `:645` — the audit-era argv short-circuit/dual-registration was removed in `2f496393`; `tests/test_cli_dograh.py`, `tests/test_cli_main_dograh.py` passed in smoke run |
| Orchestrator mode advisor sink | ✅ | `src/chatty_commander/cli/cli.py:559` `build_advisor_sink` constructs `AdvisorsService` when advisors are enabled and `:609` passes it to `ModeOrchestrator` (the audit-era `advisor_sink=None` gap was closed on 2026-06-10); `AdvisorsService.handle_message` at `advisors/service.py:198` satisfies the `AdvisorSink` protocol |
| Single CLI implementation | 🟡 | **Gap: two parallel CLI implementations still exist** — the installed script uses `cli/cli.py` (904 lines) but `python -m chatty_commander` goes through the legacy `cli/main.py` (772 lines) via `src/chatty_commander/__main__.py:29` `from .cli.main import main`; the two parsers can drift |
| Config wizard / config CLI | ✅ | `src/chatty_commander/config_cli.py`; `tests/test_config_cli.py` (suite green) |
| Voice self-test CLI | 🟡 | `src/chatty_commander/voice/cli.py` drives the real `VoicePipeline` with mock or hardware components — **gap: not registered as a `chatty-commander` subcommand; only runnable as a module** |

## Advisors / LLM

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| AdvisorsService + persistent memory + context | ✅ | `src/chatty_commander/advisors/service.py:198` `handle_message`; `advisors/memory.py:42` `MemoryStore` (JSONL persistence to `data/advisors_memory.jsonl`); `tests/test_advisors_context.py`, `tests/test_state_and_memory.py` (suite green) |
| Provider construction with stub fallback | ✅ | `src/chatty_commander/advisors/providers.py:429` `build_provider_safe` returns working stubs when the `openai-agents` SDK or API key is absent; `tests/test_real_llm_providers.py`, `tests/test_advisors_service_real_llm.py` (suite green) |
| Advisor tool registry | ✅ | `src/chatty_commander/advisors/tools/__init__.py:39` `TOOL_REGISTRY` maps `browser_analyst`, `dograh_place_call`, `switch_mode`; `tests/test_switch_mode_tool.py` passed in smoke run (landed in `4da9d523`) |
| `switch_mode` tool attached to agents | ✅ | `src/chatty_commander/advisors/providers.py:185` and `:287` append `switch_mode_tool_instance` when `tools.switch_mode.enabled` (opt-in); tool returns `SWITCH_MODE:<mode>` directives (`advisors/tools/switch_mode.py:33`) |
| `dograh_place_call` tool | ✅ | `src/chatty_commander/advisors/tools/dograh_call.py`; opt-in attach at `providers.py:173-178`; `tests/test_dograh_advisor_tool.py` (suite green) |
| AI intelligence core (text-mode conversations) | ✅ | `src/chatty_commander/ai/intelligence_core.py` wires `AdvisorsService` + `voice/enhanced_processor`; consumed by both CLIs (`cli/cli.py:817`, `cli/main.py:681`); `tests/test_intelligence_core.py` (suite green) |

## Integrations

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Dograh REST client | ✅ | `src/chatty_commander/integrations/dograh_client.py:33` `DograhHTTPError` deliberately omits request URLs from `str(e)` (internal-endpoint leak fixed in `537fbb02`); `tests/integrations/test_dograh_client.py` (suite green) |
| Dograh secret hygiene | ✅ | `scripts/seed_dograh.py:65` requires explicit `--print-secret` to emit the raw API key (fixed in `aadfafb9`); the audit-era world-readable `.env` no longer exists at the repo root (verified 2026-06-10) |
| Discord/Slack bridge | 🟡 | `src/chatty_commander/app/orchestrator.py:108` `DiscordBridgeAdapter` forwards messages to the advisor sink via `_dispatch_advisor_message` (`:277`), and the CLI now supplies a real sink — **gap: no Discord/Slack client exists in this repo (no discord dep in `pyproject.toml`); the adapter expects an external bridge process per `docs/developer/ADAPTERS.md`, and its `feed()` is currently only invoked by tests** |
| Computer-vision input | 🔲 | `src/chatty_commander/app/orchestrator.py:240` `--enable-computer-vision` selects `DummyAdapter("computer_vision")` only; no CV code in the tree (deleted in the June 2026 reset) |

## Desktop GUI / Avatar

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| GUI mode launch chain | 🟡 | `src/chatty_commander/cli/cli.py:232` `run_gui_mode` falls back avatar GUI → PyQt5 avatar → tray popup → legacy tkinter, and exits 0 gracefully when headless — **gap: `PyQt5` is not a declared dependency (only a mypy override, `pyproject.toml:215`), and no automated test launches a real GUI window** |
| Avatar GUI (pywebview TalkingHead) | 🟡 | `src/chatty_commander/avatars/avatar_gui.py` + bundled assets `src/chatty_commander/webui/avatar/index.html`; `pywebview>=4.4` is declared (`pyproject.toml:50`) — **gap: launch path untested in CI (headless); only the WS/state layers below have tests** |
| Avatar thinking-state sync over WebSocket | ✅ | `src/chatty_commander/avatars/thinking_state.py` state manager consumed by `src/chatty_commander/web/routes/avatar_ws.py:291` `@router.websocket("/avatar/ws")`; `tests/test_avatar_ws.py`, `tests/test_avatar_ws_components.py` (suite green) |
| Avatar selector / settings API | ✅ | `src/chatty_commander/web/routes/avatar_selector.py`, `avatar_settings.py`, registered via `register_shared_routers` (`server.py:147`); `tests/test_avatar_api.py`, `tests/test_avatar_launch_api.py` (suite green) |
| GUI input adapter in orchestrator | 🔲 | `src/chatty_commander/app/orchestrator.py:224` `enable_gui` appends `DummyAdapter("gui")` — GUI events never reach the command sink |

## Observability

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| Metrics registry + endpoints | ✅ | `src/chatty_commander/obs/metrics.py:323` `create_metrics_router` exposes `GET /metrics/json` and `GET /metrics/prom` (stdlib-only, thread-safe); registered in `register_shared_routers`; `tests/test_obs_metrics.py` passed in smoke run (the audit-era failure no longer reproduces) |
| Request metrics middleware | ✅ | `src/chatty_commander/web/web_mode.py:558` adds `RequestMetricsMiddleware` when obs is importable |
| Structured logging | ✅ | `src/chatty_commander/utils/logger.py`, `utils/logging_config.py`; `tests/test_structured_logging.py`, `tests/test_logger.py` (suite green) |

## Infra / CI

| Feature | Status | Evidence (verified 2026-06-10) |
|---|---|---|
| CI pipeline | ✅ | `.github/workflows/ci.yml` jobs `lint`, `test`, `frontend-build`, `performance-test`, `build`, `docker`, `notify` — YAML syntax/undefined-var/dead-reference errors fixed in `ab9fc32d` (note: ci.yml had further uncommitted edits in flight from a concurrent agent at audit time) |
| Dograh integration workflow | ✅ | `.github/workflows/dograh-integration.yml` with concurrency group + secret masking |
| Docker packaging | 🟡 | Multi-stage `Dockerfile`, `docker-compose.yml`, `docker-compose.dograh.yml` present and a `docker` CI job exists — **gap: image build/run not executed during this audit; treat as unverified** |
| PyInstaller packaging | 🟡 | `packaging/chatty_cli.spec`, `packaging/chatty_cli_lite.spec`, root `chatty-commander.spec` — **gap: no spec build was executed or verified in this audit** |
| Repo hygiene | ❌ | A tracked junk file literally named `javascript:alert('xss')` sits at the repo root (`git ls-files` confirms it is tracked); untracked clutter also present (`MagicMock/`, `htmlcov/`, root `node_modules/`, `test_results_*.txt`, and a stale `failing_tests.txt` predating the current green suite); the legacy unused `frontend/`, `server/`, and `workers/` trees have since been deleted (current app is `webui/frontend/`) |
| Test suite health | ✅ | 883 tests collected (`uv run pytest tests/ --collect-only --no-cov`); full suite green at audit time (859 run); the audit-era "93 failing tests" claim is stale — the listed failures (config env overrides, state toggle, obs metrics) no longer reproduce |
| Governance / FOSS docs | ✅ | `LICENSE` (MIT), `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, honest-status `README.md`, canonical `ROADMAP.md` (commits `cc52b876`, `c2a6ca0f`) |

## How to regenerate

This document is produced by re-running the feature audit, not by hand-editing:

1. **Inventory**: walk `src/chatty_commander/` per domain (voice, app,
   web/routes, cli, advisors, integrations, gui/avatars, obs, utils) plus
   `webui/frontend/src/` and `.github/workflows/`, listing user-facing
   features. `git log --oneline -25` first — recent commits usually invalidate
   old rows.
2. **Verify each row** by reading the cited file at the cited symbol (grep for
   the symbol name, not the line number) and asking: does the code actually do
   this, or does it stub/simulate/fall back? Mock fallbacks and
   `DummyAdapter`s are the most common source of false ✅.
3. **Run the evidence tests**:
   `uv run pytest tests/ -q --no-cov` for the full suite, or the smoke subset
   used here:
   `uv run pytest tests/test_obs_metrics.py tests/test_switch_mode_tool.py tests/test_voice.py tests/test_cli_dograh.py tests/test_web_routes_dograh.py tests/test_auth.py tests/test_audio_routes.py tests/test_preferences_routes.py tests/test_theme_routes.py tests/test_main_orchestrator.py tests/test_state_manager.py tests/test_command_executor.py -q --no-cov`
   and `cd webui/frontend && npm run build` for the frontend.
4. **Check declared dependencies**: a module can be ✅ in isolation but 🟡 for
   users if its runtime dep is missing from `pyproject.toml` `[project]`
   `dependencies`/extras (current examples: `whisper`, `pyttsx3`, `PyQt5`,
   `wakewords`).
5. Update the header date, every evidence cell, and the summary counts
   together — a row without re-verified evidence must be dropped, not carried
   forward.
