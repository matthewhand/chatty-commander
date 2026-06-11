# ChattyCommander Roadmap

**The single canonical roadmap.** Goal: take this repo to a publishable FOSS product.
`docs/developer/PRODUCTION_READINESS_ROADMAP.md` is now a pointer to this file; its still-relevant items were merged below and obsolete ones dropped.

| Tier | Meaning |
|------|---------|
| **P0** | Publish blockers — must land before announcing the repo as a usable FOSS product |
| **P1** | Quality — dead-code removal, test depth, docs accuracy |
| **P2** | Post-launch — bigger integration phases and hardening |

Progress counts in each section header count top-level checkboxes only; nesting shows partial progress on multi-part items.

---

## P0 — Publish blockers

### Security & secrets (5/6)

- [x] **`server.create_app()` attaches `AuthMiddleware`** — `/api` routes are no longer unauthenticated ([`src/chatty_commander/web/server.py:131`](src/chatty_commander/web/server.py))
- [x] **dograh `/health` body allowlisted** — only `status` and `version` keys exposed ([`src/chatty_commander/web/routes/dograh.py:28`](src/chatty_commander/web/routes/dograh.py))
- [x] **Generic `"unreachable"` reason** — route no longer interpolates the exception (and its internal hostname) into the client-visible reason ([`src/chatty_commander/web/routes/dograh.py:85`](src/chatty_commander/web/routes/dograh.py))
- [x] **`DograhHTTPError` URL scrubbing + log hygiene**
  - [x] `str(e)` omits the request URL; full URL only on `e.url` / `repr(e)` for server-side logging ([`src/chatty_commander/integrations/dograh_client.py:33`](src/chatty_commander/integrations/dograh_client.py))
  - [x] `dograh_call.py` logs `status_code` and `detail` only, never the URL ([`src/chatty_commander/advisors/tools/dograh_call.py:61`](src/chatty_commander/advisors/tools/dograh_call.py))
- [x] **`seed_dograh.py` redacts by default** — raw API key only printed with explicit `--print-secret`; `--output FILE` keeps it out of the terminal ([`scripts/seed_dograh.py`](scripts/seed_dograh.py))
- [ ] **Rotate dograh keys at the provider** — `.env` no longer exists on disk (removed from tracking in `7930a48`, git history confirmed clean), but `DOGRAH_OSS_JWT_SECRET` and `DOGRAH_API_KEY` previously sat in a world-readable file. Rotate both at the dograh deployment; when recreating `.env`, `chmod 600` it.

### Correctness — dograh CLI & wiring (4/4)

- [x] **CLI dograh routed through the main parser** — the hard-coded argv short-circuit is gone; `register_dograh_subparser` in `create_parser()` plus dispatch at [`src/chatty_commander/cli/main.py:575`](src/chatty_commander/cli/main.py)
- [x] **CLI error-branch + `--json` tests** — DograhError / generic-Exception dispatcher branches, unknown-op exit code 2, `--json` output for list/runs (`tests/test_cli_main_dograh.py`, `tests/test_cli_dograh.py`)
- [x] **`_execute_dograh_call` reason-string tests** — DograhError vs generic-Exception reason phrases pinned, plus success-log assertion (`tests/test_command_executor*.py`)
- [x] **Orchestrator `advisor_sink` actually used** — `DiscordBridgeAdapter` routes messages through it; warns when discord bridge + advisors enabled with no sink ([`src/chatty_commander/app/orchestrator.py:108,243`](src/chatty_commander/app/orchestrator.py))

### FOSS governance & packaging (8/8)

- [x] **Root `CONTRIBUTING.md`** — exists only at `docs/developer/CONTRIBUTING.md`; add a root file (can be a pointer)
- [x] **`CODE_OF_CONDUCT.md`** at root
- [x] **`SECURITY.md`** at root (vulnerability reporting policy)
- [x] **Root `CHANGELOG.md`** — exists only at `docs/developer/CHANGELOG.md`; add root file or pointer
- [x] **Fix CI workflow YAML** ([.github/workflows/ci.yml](.github/workflows/ci.yml))
  - [x] Duplicate / mis-indented `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` env entries (lines ~55-57, ~212-213)
  - [x] `${{ env.PYTHON_VERSION }}` referenced (lines ~124, ~153) but never defined in any `env:` block
- [x] **Fix README broken image** — `README.md:5` references `docs/images/dashboard.png`; the file lives at `docs/screenshots/dashboard.png`
- [x] **Version consistency** — `pyproject.toml` declares `0.2.0` but installed metadata reported `0.1.0`; reinstall/retag so published version matches
- [x] **Add the dograh block to `.env.example`** — README points users at "the dograh block in `.env.example`" (`DOGRAH_BASE_URL`, `DOGRAH_API_KEY`), but the file has no dograh keys

---

## P1 — Quality

### Web backend & API surface (5/5)

- [x] **`/api/audio/devices` + `POST /api/audio/device`** served ([`src/chatty_commander/web/routes/audio.py:94`](src/chatty_commander/web/routes/audio.py))
- [x] **`GET/PUT /api/preferences`** served ([`src/chatty_commander/web/routes/preferences.py`](src/chatty_commander/web/routes/preferences.py))
- [x] **`GET /api/themes` + `GET/POST /api/theme`** served ([`src/chatty_commander/web/routes/themes.py`](src/chatty_commander/web/routes/themes.py))
- [x] **Unify `web_mode._create_app` vs `server.create_app`** — both factories exist and both now wire auth + dograh, but they diverge in router-wiring pattern (explicit `include_router` vs `_include_optional` loop). Consolidate to one; `web_mode.py` is the production path — `server.py` should delegate or be deleted.
- [x] **Resolve remaining frontend-called endpoints with no backend** — decide implement vs delete the client methods:
  - [x] `/api/backup`, `/api/restore`
  - [x] `/api/system/restart`, `/api/system/shutdown`, `/api/system/update`, update checks
  - [x] `/api/logs`, `/api/models` (+ load/unload), `/api/command/test`
  - [x] `/api/config/export|import|reset|validate`

### Dead code — Python (4/4)

- [x] **Delete the shadow `src/chatty_commander/tools/` package** — the import-resolution footgun that caused the `..tools.X` wrong-package bug (fixed in `69a124d0`). Move the incidental CLI utilities under `advisors/tools/` or `cli/`; verify zero production imports first (only test infra references it today).
- [x] **`providers/` package orphaned** — `src/chatty_commander/providers/ollama_provider.py` has no `__init__.py` and zero importers; delete or integrate with `advisors/providers.py`
- [x] **`advisors/tools/switch_mode.py` never registered** — defined and tested but never instantiated as an advisor tool (compare `dograh_call`'s registration in `advisors/providers.py`); wire it in or remove
- [x] **`app/helpers.py` unused in production** — `ensure_directory_exists` / `format_command_output` / `parse_model_keybindings` only imported by tests; delete or integrate

### Dead code — frontend (7/7)

- [x] **Delete `LogMessageItem.tsx`** — exported, never imported (`webui/frontend/src/components/LogMessageItem.tsx`)
- [x] **Drop `classnames` dependency** — zero imports; styling is DaisyUI/Tailwind (`webui/frontend/package.json:12`)
- [x] **`web-vitals` collected but discarded** — `reportWebVitals()` called with no handler (`webui/frontend/src/index.tsx`); add a handler or remove the dependency
- [x] **Prune dead `apiService.js` methods** — backup/restore, restart/shutdown/update, logs, models load/unload, config export/import/reset/validate, testCommand remain uncalled (preferences/themes methods are now live against the new backend routes)
- [x] **Audio device "test" handlers are fake** — `handleTestMic`/`handleTestOutput` just set flags and timeout ("Simulate 3s test", `webui/frontend/src/pages/ConfigurationPage.tsx:250-258`); implement against the real audio endpoints or remove the buttons
- [x] **Remove stale repro e2e specs** — `webui/frontend/tests/e2e/reproduction.spec.ts`, `repro_ws.spec.ts`; fold useful assertions into the functional suites
- [x] **Delete legacy `frontend/web-app/`, `frontend/desktop-app/`, and root `server/` dirs** — old Next.js build artifacts; `webui/frontend/` is the only live UI. Verify no references before deleting.

### Testing (2/3)

- [x] **Python suite green** — the pre-reset backlog of 85+ failing tests (config edge cases, command executor, states, metrics) is resolved; full `uv run pytest` passes on `main`
- [x] **Frontend unit tests** — `webui/frontend/package.json` has no `test` script at all (only `test:e2e` Playwright). Add Vitest + React Testing Library and cover the providers/components that currently only have e2e coverage.
- [ ] **Raise Python coverage on thin areas** — web routes sit at 20-38%, `avatar_ws.py` at ~28% per the audit; prioritize routes that now carry auth and preference state

### Documentation (6/6)

- [x] **README "Optional: dograh voice-call integration" section** — compose overlay, `.env` block, seed script (`README.md:23`)
- [x] **Fix stale screenshot refs in `docs/user-guide/02_CONFIGURATION.md`** — lines 31/37/47/53 reference `configuration-general/models/llm/services.png` which don't exist
- [x] **Remove dead doc references** — `AVATAR_GUI.md` (from `docs/developer/WEBUI_CONNECTIVITY.md:60`), `ARCHITECTURE_OVERVIEW.md` (from `NEW_CONTRIBUTOR_GUIDE.md:36`, `ADAPTERS.md:76`); also prune the removed `/avatar/ws` docs in WEBUI_CONNECTIVITY.md
- [x] **Refresh `STRUCTURE.md` / `ARCHITECTURE.md`** — they describe `deploy/k8s/` and `server/workers/` which don't exist; active frontend is `webui/frontend/`
- [x] **Refresh `docs/developer/WEBUI_ISSUES.md`** — claims `/api/v1/audio/devices` is missing; audio, preferences, and theme endpoints now exist
- [x] **Regenerate `docs/API.md`** — stamped 2026-03-05, truncates at ~line 100, missing all `/api/v1/dograh/*` and the new audio/preferences/themes endpoints

### Telephony — dograh end-to-end (user actions) (0/3)

- [ ] **Author a real telephony workflow in dograh's UI** and document the steps
- [ ] **Configure a Twilio/Vonage provider** so `dograh_call` returns success instead of `telephony_not_configured`
- [ ] **Wire dograh's LLM / STT / TTS providers for self-hosted use** — the OSS image points all three at dograh's hosted cloud. Options: (a) OpenAI keys for all three, simplest; (b) the optional Speaches stack (local Whisper + Kokoro TTS) via `PUT /api/v1/user/configurations/user`. See `webui/frontend/tests/e2e/dograh/dograh_webcall_loopback.spec.ts` and `docs/screenshots/dograh/03-webcall-loopback.png` for the captured "blocked at LLM config" state.

---

## P2 — Post-launch

### In-browser voice testing (5/5)

Test voice functionality from the webapp as if running locally: enable the microphone in the browser and watch what the pipeline does with what you say.

- [x] **Microphone capture in the webapp** — `getUserMedia` with explicit permission UX, input-level meter, and start/stop control on a "Voice Test" page (or panel on the Audio Settings page)
- [x] **Stream browser audio to the backend** — over the existing `/ws` channel or a dedicated `/ws/audio` endpoint, feeding the same wakeword → transcription → command-matching pipeline used locally (reuses P2 WebRTC bridge groundwork below)
- [x] **Live action feedback panel** — show each pipeline stage as it happens: wake word detected → transcript → matched command → action taken (keypress/URL/system/dograh call) with success/failure and timing
- [x] **Dry-run mode (default)** — run detection and matching for real but stub action execution, reporting "would have pressed ctrl+shift+x" so remote-browser testing can't fire arbitrary system actions; explicit opt-in to live execution, auth-gated
- [x] **E2E test** — Playwright with a prerecorded audio fixture via `--use-fake-device-for-media-stream`, asserting the feedback panel shows the expected command and dry-run action

### WebRTC audio bridge (0/3)

- [ ] Bring CC's wake-word detector and dograh's pipecat audio pipeline onto a shared audio stream so a wake-word can interrupt and hand off to an in-progress dograh call
- [ ] Bidirectional state: dograh call state (`ringing`/`in-call`/`ended`) reflected in CC's `StateManager`; CC's `chatty`/`computer` mode published to dograh's session metadata
- [ ] E2E test: wake-word → dograh call → live audio → call end → CC returns to `idle`

### Production hardening (carried from PRODUCTION_READINESS_ROADMAP) (5/6)

- [x] **Secrets validation at startup** — fail fast when required env vars are missing; document all of them in `.env.example`
- [ ] **AuthN/AuthZ depth** — token refresh + revocation, role-based access (admin/user/readonly), API-key auth for service-to-service
- [x] **Structured logging** — JSON log format option, request-ID tracing (per-environment log levels already done)
- [x] **Standardized error responses** — consistent `{error, code, details, request_id}` shape; circuit-breaker/graceful-degradation for external services (LLM fallback responses already done)
- [x] **Container hardening**
  - [x] Non-root user + multi-stage Dockerfile build, `.dockerignore`
  - [x] Trivy scanning in CI
- [x] **Load testing / performance baselines**
  - [x] k6 smoke script + measured p95 baselines (`scripts/loadtest/`, all thresholds passed: p95 ≈ 3.5-4ms local)
  - [x] CI perf regression gate

Dropped as obsolete (verified against the repo): Kubernetes manifests (`deploy/` has no `k8s/` and none is planned), Celery/RQ task queue and Redis caching (no such deps in `pyproject.toml`), Alembic migrations (no DB-backed runtime models), PagerDuty/OpsGenie alerting, the avatar-GUI removal notes (already done — see "Far-from-finished features" for what remains).

### Security backlog — topics from closed bot PRs (6/6)

Distinct topics raised by the June 2026 bot-PR flood (PRs #617-#649, closed as stale/duplicate — branches targeted pre-reset code). Each needs verification against current code before acting:

- [x] **CORS restriction in `--no-auth` mode** (from #624) — check what origins the dev server allows when auth is off
- [x] **`sanitize_config_data` dictionary-key bypass** (from #626) — verify key-name masking in `utils/security.py` can't be sidestepped by nesting
- [x] **Command-injection review of command execution web path** (from #631/#632/#640) — re-audit `command_executor` shell/system actions reachable via `/api/v1/command`
- [x] **Path traversal in models route** (from #641) — confirm the #512-era fix covers `web/routes/models.py` upload/download/delete
- [x] **SSRF via DNS rebinding** (from #644) — `utils/url_validator.py` resolves-then-fetches; check TOCTOU between validation and request
- [x] **Rate limiting on command execution** (from #639) — decide whether `/api/v1/command` needs per-key throttling

### UI consolidation (0/3)

- [ ] Decide on direction: CC's React app embedded in dograh's Next.js dashboard, dograh's workflow editor embedded in CC, or a single new shell hosting both
- [ ] Single sign-on between the two services (CC uses session cookies, dograh uses X-API-Key + JWT)
- [ ] Migrate the dograh status card from polling React Query to WebSocket push on CC's existing `/ws` channel

---

## Far-from-finished features (documented, not scheduled)

These exist in the tree and are honest about their state. They are inventory, not commitments — schedule them only if a maintainer wants to own them.

- **GUI (PyQt5 avatar + tray)** — half-done, large
  - Current state: `src/chatty_commander/gui/pyqt5_avatar.py` (~390 lines) and `gui/tray_popup.py` back the `--gui` mode; wiring through the orchestrator is incomplete (GUI adapters are dummies) and there is no recent commit activity — bitrot risk.
  - Finishing would take: real GUI input adapter in the orchestrator, lifecycle/test harness for PyQt under CI (offscreen platform), packaging story for desktop.
  - Evidence: `src/chatty_commander/gui/pyqt5_avatar.py`, `src/chatty_commander/gui/tray_popup.py`, `src/chatty_commander/app/orchestrator.py` (DummyAdapter placeholders)
- **Avatar / 3D thinking-state visualization** — half-done, large
  - Current state: enum-based state machine (`avatars/thinking_state.py`), WebSocket routes (`web/routes/avatar_ws.py`, ~28% coverage) and `avatars/avatar_gui.py` exist, but there is no actual 3D rendering library — it manages avatar UI state only. The earlier 1,089-line avatar GUI was deleted in Feb 2026.
  - Finishing would take: pick a rendering target (web canvas vs PyQt), connect thinking-state transitions to the webui, cover the WS protocol with tests.
  - Evidence: `src/chatty_commander/avatars/thinking_state.py`, `src/chatty_commander/avatars/avatar_gui.py`, `src/chatty_commander/web/routes/avatar_ws.py`
- **Discord/Slack bridges** — half-done, large
  - Current state: the orchestrator's `DiscordBridgeAdapter` is now wired to route advisor messages through `advisor_sink`, but both CLI entry points still pass `advisor_sink=None` ([`src/chatty_commander/cli/cli.py:580`](src/chatty_commander/cli/cli.py), [`src/chatty_commander/cli/main.py:528`](src/chatty_commander/cli/main.py)), so `--orchestrate --enable-discord-bridge --advisors` logs a warning and drops messages. The actual bridge is an external Node process (helper at `src/chatty_commander/tools/bridge_nodejs.py`); no discord/slack deps exist in `pyproject.toml`.
  - Finishing would take: construct a real `AdvisorSink` from the advisors service in the CLI paths, ship/document the Node bridge (or replace it with a Python client), add end-to-end tests.
  - Evidence: `src/chatty_commander/app/orchestrator.py:108-279`, `src/chatty_commander/cli/cli.py:580`, `src/chatty_commander/cli/main.py:528`, `src/chatty_commander/tools/bridge_nodejs.py`
- **`llm/` module** — half-done, medium
  - Current state: four substantial files (`backends.py` ~430 lines, `processor.py` ~350, `manager.py` ~310, `cli.py` ~345) but only `get_global_llm_manager()` is consumed (by `advisors/service.py`); `CommandProcessor` and `llm/cli.py` have no external callers.
  - Finishing would take: either fold the useful manager pieces into `advisors/` and delete the rest, or integrate `CommandProcessor` into the command pipeline and expose the CLI.
  - Evidence: `src/chatty_commander/llm/__init__.py`, `src/chatty_commander/llm/manager.py`, `src/chatty_commander/advisors/service.py`
- **Config system (JSON + `CHATCOMM_*` env overrides)** — half-done, medium
  - Current state: `app/config.py` (~700 lines) loads JSON config with env-var overrides and a default-config generator. The audit flagged thin/edge-case validation (path traversal, null values, env endpoint/audio overrides); the suite is green now but coverage of those edges is shallow, and the YAML support some docs imply does not exist.
  - Finishing would take: a schema-validated config layer (pydantic-settings), documented precedence rules, and the `.env.schema`/`.env.example` completeness item from P0.
  - Evidence: `src/chatty_commander/app/config.py`, `src/chatty_commander/app/default_config.py`, `tests/test_config*.py`

---

## Repo hygiene (0/2)

- [ ] **Delete 13 unmerged orphaned remote branches** — stale Aug-Sep 2025 bot experiments with no open PRs (verify with `git branch -r --no-merged main`). Owner to run:

  ```bash
  git push origin --delete codex/add-opentelemetry-setup-in-telemetry.ts
  git push origin --delete codex/create-ascii-encoder/decoder-and-update-canvas-builder
  git push origin --delete codex/expand-chatpane-with-new-features
  git push origin --delete codex/expand-sidecarpane-with-header-and-tabs
  git push origin --delete codex/extend-sse-support-for-logs
  git push origin --delete codex/implement-canvas-api-and-iframe-message-bridge
  git push origin --delete codex/implement-signed-urls-api-endpoint
  git push origin --delete codex/introduce-csp-headers-middleware
  git push origin --delete codex/modify-tests-to-import-shared-module
  git push origin --delete codex/update-import-path-in-canvas-builder
  git push origin --delete dependabot/github_actions/actions/checkout-5
  git push origin --delete feature/test-improvements
  git push origin --delete st00br-codex/add-environment-variable-checks-and-tests
  ```

- [ ] **Delete 8 already-merged remote branches** — fully contained in `main` (verify with `git branch -r --merged main`), safe to remove:

  ```bash
  git push origin --delete codex/replace-stub-with-streaming-events
  git push origin --delete dependabot/github_actions/actions/setup-python-6
  git push origin --delete dependabot/github_actions/actions/upload-pages-artifact-4
  git push origin --delete dependabot/github_actions/codecov/codecov-action-5
  git push origin --delete dependabot/npm_and_yarn/tests/tsx-4.20.6
  git push origin --delete dependabot/pip/bcrypt-5.0.0
  git push origin --delete dependabot/pip/onnx-1.19.0
  git push origin --delete feat/fix-final-tests
  ```

---

## Done (recent)

2026-06-10 (this sprint, all on `main`):

- ✅ `server.create_app()` now attaches `AuthMiddleware`; dograh internals no longer leak (`0ec4feb4`)
- ✅ dograh `/health` allowlist (`status`/`version` only) + generic `"unreachable"` reason (`0ec4feb4`)
- ✅ `DograhHTTPError` messages scrubbed of internal URLs; `dograh_call` logs status/detail only (`537fbb02`)
- ✅ CLI dograh routed through the main parser — argv short-circuit removed; error-branch and `--json` tests added (`2f496393`)
- ✅ Command-executor dograh reason strings and success log pinned by tests (`0ce4e9a9`)
- ✅ Orchestrator `advisor_sink` wired via `DiscordBridgeAdapter` (`301236ae`)
- ✅ `seed_dograh.py` redacts the API key unless `--print-secret`; README gained the dograh section (`aadfafb9`)
- ✅ `/api/audio/devices` + `/api/audio/device` endpoints the webui already calls (`d1b496a2`)
- ✅ `/api/preferences` GET/PUT, `/api/themes`, `/api/theme` endpoints (`2f4c12c8`)
- ✅ Full Python test suite green on `main`; frontend builds

Earlier (dograh phase 1 foundation):

- ✅ Dograh OSS docker overlay (`docker-compose.dograh.yml`) — 5-service stack on remapped ports, opt-in via `COMPOSE_FILE`
- ✅ End-to-end Python client (`integrations/dograh_client.py`) with `X-API-Key` auth, structured errors, 99% test coverage
- ✅ `cc dograh {health,list,call,show,runs,run-info}` CLI subcommand group
- ✅ Wake-word → `dograh_call` action wired into `CommandExecutor`
- ✅ Advisor LLM tool (`dograh_place_call`) wired into `CompletionProvider`
- ✅ FastAPI routes `/api/v1/dograh/{status,workflows}` with graceful degradation
- ✅ React `DograhStatusCard` on the dashboard with online + offline states (Playwright screenshots captured)
- ✅ CI workflow (`.github/workflows/dograh-integration.yml`) with secret masking and seed bootstrap
- ✅ Two latent silent-registration bugs caught and fixed (`69a124d0` advisors tools import path, `48017506` CLI subcommand dispatch)
- ✅ `.env` with live dograh secrets removed from disk and from tracking (`7930a48`); history verified clean
- ✅ Main reset to healthy baseline after 35+ syntax errors from unvetted bot PRs (`3ac5ea05`); dead vision/dance/QA-fleet subsystems deleted
