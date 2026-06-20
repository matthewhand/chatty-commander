# ChattyCommander Roadmap

**Front and center:** See our [Vision](https://github.com/matthewhand/chatty-commander/blob/main/docs/developer/ARCHITECTURE.md#vision) in ARCHITECTURE.md (plus honest assessment of what is built vs. what remains, and Archived/Legacy Architectures section).

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
- [x] **Raise Python coverage on thin areas** — done across several waves: ws.py/llm/manager/lifecycle/avatar routes → ~100% (#671), llm·voice·cli surfaces (#682), and voice self_test/enhanced_processor/orchestrator/transcription (#686). Web routes that carry auth/preferences are now well-covered. A latent `sys.modules['numpy']` test-isolation leak surfaced along the way was also fixed (#687).

### Documentation (6/6)

- [x] **README "Optional: dograh voice-call integration" section** — compose overlay, `.env` block, seed script (`README.md:23`)
- [x] **Fix stale screenshot refs in `docs/user-guide/02_CONFIGURATION.md`** — lines 31/37/47/53 reference `configuration-general/models/llm/services.png` which don't exist
- [x] **Remove dead doc references** — `AVATAR_GUI.md` (from `docs/developer/WEBUI_CONNECTIVITY.md:60`), `ARCHITECTURE_OVERVIEW.md` (from `NEW_CONTRIBUTOR_GUIDE.md:36`, `ADAPTERS.md:76`); also prune the removed `/avatar/ws` docs in WEBUI_CONNECTIVITY.md
- [x] **Refresh `STRUCTURE.md` / `ARCHITECTURE.md`** — they describe `deploy/k8s/` and `server/workers/` which don't exist; active frontend is `webui/frontend/`
- [x] **Refresh `docs/developer/WEBUI_ISSUES.md`** — claims `/api/v1/audio/devices` is missing; audio, preferences, and theme endpoints now exist
- [x] **Regenerate `docs/API.md`** — stamped 2026-03-05, truncates at ~line 100, missing all `/api/v1/dograh/*` and the new audio/preferences/themes endpoints

### Telephony — dograh end-to-end (user actions) (0/3)

> ⛔ **Blocked on external resources (cannot be completed in-repo).** Requires a live dograh deployment plus a real Twilio/Vonage account + provider credentials. These are operator actions, not code.

- [ ] **Author a real telephony workflow in dograh's UI** and document the steps
- [ ] **Configure a Twilio/Vonage provider** so `dograh_call` returns success instead of `telephony_not_configured`
- [ ] **Wire dograh's LLM / STT / TTS providers for self-hosted use** — the OSS image points all three at dograh's hosted cloud. Options: (a) OpenAI keys for all three, simplest; (b) the optional Speaches stack (local Whisper + Kokoro TTS) via `PUT /api/v1/user/configurations/user`. See `webui/frontend/tests/e2e/dograh/dograh_webcall_loopback.spec.ts` and `docs/screenshots/dograh/03-webcall-loopback.png` for the captured "blocked at LLM config" state.

### Deterministic dograh call proof — TTS audio loopback (0/3)

> ⛔ **Partially blocked.** The audio fixture + fake-mic Chromium wiring are codeable, but a green assertion needs a dograh instance with LLM/STT/TTS providers configured — which depends on the blocked telephony setup above.

Prove dograh's full audio pipeline (STT → LLM → TTS) works without a human, a phone, or Twilio, by feeding a scripted utterance in and asserting on what comes out. Builds on the existing `smallwebrtc` loopback spec. **Prerequisite: the STT/TTS/LLM providers above must be wired first** — this removes the human and the phone, not the provider requirement.

- [ ] **Generate the input audio** — TTS a fixed utterance (e.g. "I'd like to book an appointment") to a 16-bit PCM WAV fixture, committed under `tests/fixtures/audio/`. Any TTS works (OpenAI, Piper/Kokoro, even `say`); the audio is the test input, not a provider dependency.
- [ ] **Feed it as the call's microphone** — launch Chromium with `--use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<fixture>.wav` so the `smallwebrtc` call leg "hears" the fixture instead of a live mic (extends `dograh_webcall_loopback.spec.ts`).
- [ ] **Assert on the response, not exact strings** — read the run transcript via `DograhClient.get_workflow_run(workflow_id, run_id)` and assert the STT picked up the intent (keyword/intent match, since STT is non-deterministic) and the agent produced a TTS reply turn. Optionally capture the outbound WebRTC audio and re-transcribe for a fuller assertion. This turns the today-manual loopback into a CI-gateable check.

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

> ⛔ **Blocked on a live dograh instance** (shared audio stream, run-state vocabulary confirmation) and, for the outbound mode→dograh metadata item, on a dograh API that does not yet exist.

Spike + feasibility: [`docs/developer/WEBRTC_BRIDGE_SPIKE.md`](docs/developer/WEBRTC_BRIDGE_SPIKE.md). **Phase-0 state bridge landed (#680)** — see the nested item below.

- [ ] Bring CC's wake-word detector and dograh's pipecat audio pipeline onto a shared audio stream so a wake-word can interrupt and hand off to an in-progress dograh call
- [ ] **Inbound call-state bridge (state-only)** — dograh call state (`ringing`/`in-call`/`ended`) surfaced in CC
  - [x] Poller + `dograh_call_state` `/ws` broadcast + `GET /api/v1/dograh/call-state` (#680, wired-but-dormant)
  - [ ] Confirm the dograh run-state field/vocabulary against a live instance (two constants in `dograh_call_state.py`)
  - [x] Call `start_dograh_call_poller` when a run becomes active — `POST /api/v1/dograh/call-state/track`/`untrack` (#684) + **auto-start on `initiate_call`** so it lights up without a manual call (#688); frontend dashboard CallStateBadge consumes the `dograh_call_state` broadcast (#684)
  - [ ] Outbound: publish CC's `chatty`/`computer` mode into dograh session metadata (no dograh API for this yet — blocked)
- [ ] E2E test: wake-word → dograh call → live audio → call end → CC returns to `idle`

### Production hardening (carried from PRODUCTION_READINESS_ROADMAP) (5/6)

- [x] **Secrets validation at startup** — fail fast when required env vars are missing; document all of them in `.env.example`
- [ ] **AuthN/AuthZ depth** — implementing [`docs/developer/AUTHZ_DESIGN.md`](docs/developer/AUTHZ_DESIGN.md) phase by phase (opt-in; default/`--no-auth` unchanged throughout):
  - [x] **Phase 1 — token refresh + jti revocation** (#690): login also returns a refresh token, `POST /api/v1/auth/refresh` rotates, in-memory self-pruning denylist (sqlite seam left for later), logout revokes
  - [x] **Phase 2 — role-based access** (admin/user/readonly via a `require_role` dependency) (#692) — additive, pass-through when auth inactive; guards PUT /config (admin) + POST /command (user)
  - [x] **Phase 3 — scoped service-to-service API keys** (#693) — legacy key stays wildcard; named `auth.service_keys` opt-in; `require_scope` guards POST /state
  - [x] **Phase 4 — optional persistent (sqlite) revocation store** — `SqliteRevocationStore` in `web/revocation.py` (sqlite denylist, self-pruning by `exp`, survives restart); selected via `auth.revocation_store: "memory" | "sqlite"` (default `memory`) wired in `web/server.py`
  Two gaps surfaced during the survey, both already fixed:
  - [x] **Frontend login is a dead path** (fixed #678) — `authService.ts` POSTs `/api/v1/auth/login` + `/api/v1/auth/me` (expects `roles[]`) but no backend route implements them; an auth-enabled deployment cannot log in (today only the no-auth probe works)
  - [x] **`web_server.auth_enabled` is disconnected from the middleware** (fixed #678 — CHATTY_API_KEY wired + fail-fast) — `config.py` never populates `auth.api_key`; with `auth_enabled=True` and no hand-written key, every `/api` request 401s. Wire a key source (env `CHATTY_API_KEY` + schema) or make the flag honest
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

> ⛔ **Blocked on a cross-product decision + dograh's Next.js app.** Embedding CC's React app in dograh's dashboard (or vice-versa) and SSO between the two services are architectural choices for the maintainer, not self-contained code tasks.

- [ ] Decide on direction: CC's React app embedded in dograh's Next.js dashboard, dograh's workflow editor embedded in CC, or a single new shell hosting both
- [ ] Single sign-on between the two services (CC uses session cookies, dograh uses X-API-Key + JWT)
- [x] Migrate the dograh status card from polling React Query to WebSocket push on CC's existing `/ws` channel — `/ws` pushes a `dograh_status` frame (same `{available, reason, health}` shape as `GET /api/v1/dograh/status`) on connect (via `include_ws_routes(get_initial_messages=...)` → `WebModeServer._initial_ws_messages`) and on call-tracking start (`broadcast_dograh_status`); `DograhStatusCard.tsx` subscribes to it and dropped its `refetchInterval` (REST kept for initial-load fallback). Tests: `tests/unit/test_websocket_routes.py::TestWebSocketInitialMessages`, `tests/e2e/test_web_mode.py::...test_websocket_pushes_dograh_status_on_connect`, `webui/frontend/src/components/DograhStatusCard.test.tsx`

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

## UX & polish backlog (from 2026-06-18 UI/UX audit)

Synthesised from a per-page + cross-cutting critique of `webui/frontend` (every
page, the layout shell, theming, accessibility and the end-to-end workflows).
Deduplicated and prioritised. P0 = broken or blocks use; P1 = clear quality gap;
P2 = polish.

### P0 — broken / blocking (8/8)

- [x] **`ScrollToTop` never works** — it listens on `window` scroll, but the scroll container is `<main class="overflow-y-auto">` inside an `h-screen overflow-hidden` shell, so the window never scrolls; attach the listener + `scrollTo` to `<main>` ([`ScrollToTop.tsx`](webui/frontend/src/components/ScrollToTop.tsx), [`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#711)
- [x] **Live-region a11y is absent app-wide** — toasts, dashboard/login error alerts, the real-time command log and WebSocket status all update silently; screen-reader users get no feedback. Wrap `ToastProvider` in `role=region aria-live=polite` (assertive for errors) + dismiss button; add `role=alert` to error alerts and `role=log aria-live=polite` to the command log ([`ToastProvider.tsx`](webui/frontend/src/components/ToastProvider.tsx), `DashboardPage.tsx`, `LoginPage.tsx`)  ✅ (#711)
- [x] **Modals are not real dialogs** — the Command-Authoring confirm modal and the mobile sidebar are hand-rolled `motion.div`s with no `role=dialog`/`aria-modal`, no focus trap, no Escape-to-close, no focus return; keyboard/SR users are stranded ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx), [`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#712)
- [x] **Theme changes don't persist** — `setTheme` mutates the live DOM but is never written back to config/`localStorage`, so a refresh reverts it; also no theme switcher in the layout shell ([`ThemeProvider.tsx`](webui/frontend/src/components/ThemeProvider.tsx))  ✅ (#711)
- [x] **Session/auth expiry is unhandled** — `useAuth` only checks on mount; a token expiring mid-session yields silent 401s with no redirect to `/login` and the WS stops after 10 retries with no re-auth prompt. Centralise 401 handling (clear token + redirect + toast) ([`useAuth.tsx`](webui/frontend/src/hooks/useAuth.tsx), [`WebSocketProvider.tsx`](webui/frontend/src/components/WebSocketProvider.tsx))  ✅ (#713)
- [x] **No first-run/onboarding** — a fresh user lands on an empty dashboard ("Waiting for commands…") with no guidance toward Commands → New Command → Voice Test; add a dismissible onboarding callout ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#713)
- [x] **Authoring can silently clobber commands** — `saveCommand` read-modify-writes the whole config with no name-collision check, so a new author can overwrite a built-in; edit-mode rename also orphans the old key. Warn/block on collision; lock or handle rename ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#712)
- [x] **No global error boundary** — a thrown render error white-screens the whole app; wrap routed pages in an ErrorBoundary with a branded fallback + route-loading skeleton ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#711)

### P1 — quality (19/19)

- [x] **CSS theme-token inconsistency** — dozens of rules use `hsl(var(--x))` (the exact bug that made gradient headings transparent, already fixed for `.text-gradient-*` via `oklch`); migrate all `hsl(var(--x))` → `oklch(...)`, and drive glassmorphism/scrollbar/dropdown backgrounds from DaisyUI tokens instead of hardcoded dark `rgba(...)` so non-dark themes render correctly ([`index.css`](webui/frontend/src/index.css))  ✅ (#712)
- [x] **Active-nav defined twice, conflictingly** — `MainLayout` sets inline `border-l-4 bg-primary/20` while `index.css .menu li>a.active` sets a different gradient/border; pick one source of truth and ensure a non-color cue + adequate contrast on neon themes ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx), `index.css`)  ✅ (#711)
- [x] **No persistent app header** — page title, breadcrumb and global status/theme/account controls live inside scrolling `<main>` and scroll away; add a sticky desktop header with a standard page-header slot ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx), [`Breadcrumbs.tsx`](webui/frontend/src/components/Breadcrumbs.tsx))  ✅ (#713)
- [x] **Login polish** — error not announced/focused, password not cleared or refocused on failure, no show/hide password toggle, no `autoComplete` hints, and the helper text leaks internal CLI flags (`--no-auth`) to end users; also network-down vs bad-credentials are indistinguishable ([`LoginPage.tsx`](webui/frontend/src/pages/LoginPage.tsx), [`authService.ts`](webui/frontend/src/services/authService.ts))  ✅ (#711)
- [x] **Dashboard has no "is my voice assistant working right now?" signal** — add a primary Voice/Listening status card (mic active + state-machine mode: idle/computer/chatty) above the stats grid ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#711)
- [x] **WebSocket card shows stale-but-green** — `lastMsgAgo` can read "120m ago" while styled "Connected"; downgrade to a warning tint past a staleness threshold; add a header-level "live · updated Xs ago" freshness stamp ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#711)
- [x] **PerformanceChart is unreadable** — X-axis is `hide`, no visible legend, series distinguished by colour only; show sparse time ticks + a `<Legend />` and a "last N min" caption ([`PerformanceChart.tsx`](webui/frontend/src/components/PerformanceChart.tsx))  ✅ (#711)
- [x] **Radial CPU/Memory gauges lack `aria-value*`** and round differently from the adjacent numeric value; add `aria-valuenow/min/max` + `aria-label`, unify rounding ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#711)
- [x] **Dograh-offline reads as failure** — the not-configured state is styled identically to a real error; use a neutral/info treatment with a "Set up" affordance, distinct from error ([`DograhStatusCard.tsx`](webui/frontend/src/components/DograhStatusCard.tsx))  ✅ (#711)
- [x] **Commands list doesn't scale** — 2-up tall cards waste space and don't scan; each repeats an identical fake "REST API Trigger" block; no sort/pagination; type isn't badged; edit/delete buried in a kebab. Switch to a dense table/list with per-type badge+icon, sort, surfaced edit/delete, and a page-level trigger note ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#712)
- [x] **Commands uses `window.alert()`** for delete/import failures (jarring, bypasses the toast system) and the advertised Ctrl+K shortcut has no handler; route errors through `useToast`, wire Ctrl/Cmd+K to focus search ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#712)
- [x] **Import JSON silently replaces the whole command set** with no confirm/diff (both Commands import and Authoring save); add a confirm step showing added/removed/changed counts ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx), `CommandAuthoringPage.tsx`)  ✅ (#712)
- [x] **Authoring has no danger warnings, test, or examples** — no heuristic warning on risky shell (`rm -rf`, `curl|sh`) or non-https URLs, no per-action dry-run/preview, no format examples/help for keypress/url/shell; add inline danger badges, a Test affordance, and per-type helper text ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#712)
- [x] **Authoring is a dead-end** — on save it resets in place with no success toast/confirmation and no navigation to the new command; AI-mode and Manual-mode have asymmetric fields/validation. Navigate to `/commands` (or toast + "View command") on success; unify the two modes ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#712)
- [x] **Configuration has no dirty-state or unsaved-changes guard** — Save is always enabled, success/failure feedback is a tiny grey glyph (and `persistConfig` doesn't check `res.ok`); add dirty tracking, a Discard button, a `beforeunload`/route-leave guard, and a real toast on save ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#712)
- [x] **Configuration lacks structure & help** — one long scrolling card; group into tabs (General / Audio / Voice Models / LLM) with a sticky Save bar; add tooltips for technical options (target state, inference framework, wake-word model states); confirm before deleting a voice model; label the device `<select>`s ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#712)
- [x] **Voice Test can't select a mic and gives false confidence** — no device picker, "streaming" wording shows even when the recorder failed or the WS is down, wake-word detection has no distinct feedback, and there's no transcript panel; add a device `<select>`, gate "streaming" on real recorder+WS state, a distinct wake-word affordance, and a transcript surface ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#712)
- [x] **Author → test journey has no connective tissue** — nothing links a new command to Voice Test and back; add a "Test this command" action on command cards and an "Edit commands" link on Voice Test ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx), [`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#712)
- [x] **DynamicDropdown menu lacks keyboard semantics** — no `role=menu`/`menuitem`, no Escape, no arrow-key roving focus; add them ([`DynamicDropdown.tsx`](webui/frontend/src/components/DynamicDropdown.tsx))  ✅ (#711)

### P2 — polish (10/10)

- [x] **Stale screenshots** — `docs/screenshots/*.png` show UI not in the current code (a 4-step authoring stepper, a Theme Preview panel, a "Voice Pipeline" toggle, star "RELIABILITY" ratings); regenerate the screenshots and reconcile any genuinely-missing controls ([`tests/e2e/guided_tour.spec.ts`](webui/frontend/tests/e2e/guided_tour.spec.ts))  ✅ (#712)
- [x] **Inconsistent control sizing** across pages (`select`/`select-sm`/`select-xs`, mixed toolbar button heights); standardise a size scale ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx), `CommandsPage.tsx`)  ✅ (#714)
- [x] **Dashboard hero pushes telemetry below the fold** — make the welcome hero compact/dismissible or move it below the stats grid ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#712)
- [x] **Command-log rows keyed by array index** on a rolling window (key collisions); key on a stable id ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#712)
- [x] **Two parallel notification systems** (framer-motion toasts vs CSS `.alert`) with different motion/placement; unify on one ([`ToastProvider.tsx`](webui/frontend/src/components/ToastProvider.tsx), `index.css`)  ✅ (#714)
- [x] **Brand identity is thin & inconsistent** — "Chatty / Voice Commander" (sidebar) vs "Chatty Commander" (login/mobile), no logo mark; design one logo lockup used everywhere ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx), `LoginPage.tsx`)  ✅ (#713)
- [x] **`index.css` is borrowed** ("Open Hivemind — Modern UI Styles" header) and overrides DaisyUI element defaults broadly; re-home it and prefer component classes over blanket `.card/.btn/.table` overrides ([`index.css`](webui/frontend/src/index.css))  ✅ (#712)
- [x] **Motion isn't reduced-motion-aware** — focus/hover `translateY`, card lift/glow, row translate, progress pulse, unbounded list-stagger delay all animate unconditionally; gate behind `prefers-reduced-motion` and cap the stagger ([`index.css`](webui/frontend/src/index.css), `CommandsPage.tsx`)  ✅ (#712)
- [x] **Breadcrumb "Home › Dashboard" duplication** and missing deep-route labels; dedupe Home and complete `pathNameMap` ([`Breadcrumbs.tsx`](webui/frontend/src/components/Breadcrumbs.tsx))  ✅ (#712)
- [x] **Theme set is small & samey** — only `light, dark, cyberpunk, synthwave` (3 are neon/purple); curate an intentional set incl. a neutral high-contrast option, verified against the CSS-token fixes above ([`tailwind.config.js`](webui/frontend/tailwind.config.js))  ✅ (#713)

---

## UX backlog — round 2 (from 2026-06-19 re-audit of the post-wave-4 UI)

Deeper pass over the improved UI (5 agents: aesthetics, deep interaction/edge
cases, responsive, a11y+design-system, workflows+perf). Several P0s are
**regressions the fix-waves introduced** — fix first.

### P0 — regressions & broken (9/9)

- [x] **Theme switcher shows raw token names** — `THEME_LABELS` (MainLayout) still maps the removed `cyberpunk`/`synthwave`, so `corporate/business/emerald/nord` fall through to lowercase ids; key the labels to `AVAILABLE_THEMES` + title-case fallback ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#716)
- [x] **Config "General" theme `<select>` lists dead themes** — it hardcodes `dark/light/cyberpunk/synthwave`; picking cyberpunk/synthwave sets a non-existent `data-theme`, and the 4 real themes are missing. Drive the options from `AVAILABLE_THEMES`/`useTheme()` ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#716)
- [x] **Duplicate page title (two `h1`s)** — the sticky desktop header `h1` duplicates each page's own hero `h1`/`h2` directly below it (visual + heading-order a11y); make the header the single source of truth (hide page hero title on `lg`, or demote) ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx) + pages)  ✅ (#716)
- [x] **Duplicate breadcrumb on desktop** — Breadcrumbs render in the sticky header AND again in the page body on `lg`; render one instance ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#716)
- [x] **author→test deep-link is a no-op** — Commands "Test this command" links to `/voice-test?command=<name>` but VoiceTest never reads the param; read it and prefill/auto-send + a "Testing: <name>" banner ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#716)
- [x] **WS reconnect-exhausted is dead state** — `WebSocketProvider` exposes `reconnectExhausted`/`reconnect()` but no UI consumes them; after 10 attempts the user is dead-ended. Surface a "Reconnect" button in the dashboard WS card + command-log offline notice ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)
- [x] **Commands table has no mobile fallback** — only `overflow-x-auto`; at ~375px the Actions column scrolls off-screen. Add a stacked-card list `md:hidden`, table at `md+` ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#716)
- [x] **Config tabs overflow on mobile** — `tabs tabs-bordered` non-wrapping row clips "LLM" at ~360px; add `overflow-x-auto`/scroll or a `max-sm` `<select>` ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#716)
- [x] **Expiry mid-form destroys unsaved edits** — a 401 (incl. background polling) clears auth and unmounts the form via ProtectedRoute with no guard; defer redirect when a dirty form/modal is open, or stash a returnTo+draft ([`useAuth.tsx`](webui/frontend/src/hooks/useAuth.tsx), [`apiService.js`](webui/frontend/src/services/apiService.js))  ✅ (#721)

### P1 — quality (11/13)

- [x] **VoiceTest brand inconsistency** — its sidebar/header shows a stacked "Chatty / Voice Commander" lockup instead of the shared `Logo` ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#716)
- [x] **Config & Authoring tabs miss the APG keyboard pattern** — `role=tab` present but no roving `tabIndex` / Arrow/Home/End handling ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx), [`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#717)
- [x] **`:focus-visible` ring uses `--p` (primary)** — invisible on `bg-primary` surfaces (active nav, primary buttons, active tab); use `--bc`/contrasting halo + offset ([`index.css`](webui/frontend/src/index.css))  ✅ (#716)
- [x] **Config tab state not persisted/deep-linkable**; back `?tab=` (and persist Commands `?sort=`) via `useSearchParams` ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx), [`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#717)
- [x] **Mic test stream leaks on tab/route change** — leaving the Audio tab doesn't stop an in-progress `getUserMedia` test; clean up on tab change/unmount ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#716)
- [x] **Config seeds once → stale-write risk** — never re-seeds baseline on refetch/refocus, so it can show "All saved" against stale data and clobber a newer remote config; re-seed when clean, warn when dirty ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#716)
- [x] **`handleFetchModels` swallows errors** — a thrown fetch (bad URL/key/CORS) shows nothing; add catch→toast/error state ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#716)
- [x] **Commands sortable-looking headers are inert** — make Name/Type `<th>` buttons with `aria-sort`; add table `<caption>`/aria-label + `aria-live` on the "Showing N of M" count ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#716)
- [x] **Dashboard double data source** — polls `/health` every 5s AND consumes WS push for the same CPU/mem/mode; suspend polling when WS is fresh, fall back when stale ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)
- [x] **Dashboard re-renders whole tree on every telemetry/log frame** — split telemetry + command-log + chart into memoized children / bail on unchanged values; `React.memo` PerformanceChart ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)
- [ ] **Command table not virtualized + animates every row** — windowing for large sets; drop `motion.tr` past the stagger cap ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))
- [ ] **No reusable Button/Card/Field primitives** — card/field/button class clusters are copy-pasted with drift; extract shared components ([`webui/frontend/src/components`](webui/frontend/src/components))
- [x] **Multi-tab + background-poll auth desync** — expiry isn't broadcast across tabs (no `storage` listener); polling keeps running after logout and can force-expire a fresh login; reset latch on `getCurrentUser` success and cancel polls when unauthenticated ([`authService.ts`](webui/frontend/src/services/authService.ts), [`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)

### P2 — polish (12/12)

- [x] **Gradient `h1` + gradient buttons/badges everywhere** dilute emphasis — reserve the gradient for one hero; solid `text-base-content` for routine titles ([`index.css`](webui/frontend/src/index.css))  ✅ (#717)
- [x] **Stat-card icons are a random rainbow** — standardize to a muted accent or status-driven color ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#717)
- [x] **Voice Assistant card leaks placeholder strings** ("Mic: unknown · current mode") — render a real value or a clean "Not detected" ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)
- [x] **Radial gauges read as broken arcs** — use a full-track radial-progress with centered label ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#716)
- [x] **Emoji section-icons mixed with lucide line icons** — unify on lucide ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx), pages)  ✅ (#718)
- [x] **Login double-branding** — big avatar mark + full Logo lockup (which includes the mark) shown together; keep one ([`LoginPage.tsx`](webui/frontend/src/pages/LoginPage.tsx))  ✅ (#717)
- [x] **Icon sizes ad-hoc (12–32)** — define sm/md/lg scale ([`webui/frontend/src`](webui/frontend/src))  ✅ (#718)
- [x] **Shadows use raw `rgba(0,0,0,…)`** (too heavy on light themes) — token from `--bc`/`--b3` ([`index.css`](webui/frontend/src/index.css))  ✅ (#716)
- [x] **Radius scale inconsistent** (`rounded` vs `-lg`/`-xl`/`-box` + raw rem) — standardize ([`index.css`](webui/frontend/src/index.css))  ✅ (#717)
- [x] **No bulk ops on Commands** (select-all, multi-delete, export-selected) ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#717)
- [x] **Dead `.menu li>a.active` CSS** (component opts out) — delete ([`index.css`](webui/frontend/src/index.css))  ✅ (#716)
- [x] **Onboarding never reappears** when the user returns to a true empty state; re-show on `hasNoCommands` or add a "show getting started" affordance ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#717)

---

## UX backlog — round 3 (from 2026-06-20 re-audit, post-wave-8)

Deeper pass that found real bugs (several in the recent session-modal + bulk-ops
work). Fix highest-confidence bugs first.

### P0/P1 — real bugs (13/13)

- [x] **Clearing search wipes the sort** — the X / "Clear search" calls `setSearchParams({})`, discarding `?sort`/`?dir`; build from `prev` and only delete `q` ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Bulk delete aborts on partial failure** — sequential `await` with no per-item catch; a mid-loop failure skips the rest, mis-reports total failure, leaves stale selection. Use `Promise.allSettled`, refetch unconditionally, clear only succeeded names, report "Deleted X, failed Y" ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Import/export shape incompatible** — export emits the flat `/api/v1/commands` shape but import only accepts `actions[]`/legacy, so the app's own export is rejected on re-import; and `actions[]` commands don't render type/detail in the table. Normalize one schema on read+write ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Single delete doesn't deselect** — a deleted command stays in `selected`, so the bulk bar lingers and a later bulk delete 404s; remove it from the set on delete success ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Duplicate Ctrl/Cmd+K handlers** — MainLayout (navigate to /commands) and CommandsPage (focus search) both bind it and both fire on /commands; consolidate (MainLayout focuses search when already on /commands; drop the CommandsPage one) ([`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx), [`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **SessionExpiredModal "Dismiss" traps the user on a dead page** — hides the modal but leaves `user` set + token gone, so the page looks logged-in while every call 401s and re-summons the modal. After dismiss show a persistent "Session expired — sign in to save" banner; disable the page's save bar while blocking ([`useAuth.tsx`](webui/frontend/src/hooks/useAuth.tsx), [`SessionExpiredModal.tsx`](webui/frontend/src/components/SessionExpiredModal.tsx), [`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#723)
- [x] **Session-modal copy oversells recovery** — "your unsaved changes are still here" but the token is already cleared so a save re-401s; reword honestly ("Copy your changes before signing in") and relabel the ambiguous "Dismiss" ([`SessionExpiredModal.tsx`](webui/frontend/src/components/SessionExpiredModal.tsx))  ✅ (#723)
- [x] **Theme source-of-truth drift** — the sidebar ThemeSwitcher (`useTheme`/localStorage) and Configuration's Theme `<select>` (`config.theme` from backend) are independent and can show different values at once; make Config read live `useTheme().theme` ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx), [`MainLayout.tsx`](webui/frontend/src/components/MainLayout.tsx))  ✅ (#723)
- [x] **Config seeds in the render body** (re-flagged) — `setConfig`/`setBaseline` run during render off `remoteConfig`; a background refetch mid-edit can clobber in-flight edits. Move to a `useEffect` keyed on the remote JSON ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#723)
- [x] **CommandAuthoring isDirty false-positive** — typing one char into the AI description marks dirty (triggers the unsaved-changes deferral) with no savable work; only treat AI dirty when `generatedCommand !== null` ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#723)
- [x] **CommandAuthoring isDirty false-negative** — the manual baseline is the raw server shape, not normalized through `saveCommand`'s mapper, so edit-then-revert reads as phantom dirty; normalize the loaded baseline through the same mapper ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#723)
- [x] **VoiceTest prefill auto-send not reset on auto-reconnect** — `autoSentRef` is only reset in manual `reconnect()`, so after a transient drop the "Testing: <name>" banner lies (no re-test); reset on each fresh `onopen`. Also clamp `deltaMs >= 0` and don't clear the input for an auto-sent prefill ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#723)
- [x] **CommandAuthoring collision guard uses a stale snapshot** — `existingNames` fetched once on mount; re-fetch at save time so a concurrently-created key isn't silently clobbered ([`CommandAuthoringPage.tsx`](webui/frontend/src/pages/CommandAuthoringPage.tsx))  ✅ (#723)

### P2 — responsive / perf / polish (9/9)

- [x] **Commands header buttons overflow on phones** — `flex` no-wrap clips Refresh/Export/Import/New; add `flex-wrap` (or icon-only `<sm`) ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Bulk-action bar not sticky** — scrolls off-screen on long mobile lists; `sticky` it ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Bulk-bar `aria-live` too broad** — wraps the buttons too, re-announcing on every toggle; scope it to the "{n} selected" count ([`CommandsPage.tsx`](webui/frontend/src/pages/CommandsPage.tsx))  ✅ (#723)
- [x] **Config tooltips overflow on mobile** — `tooltip-right` near the right edge clips; make direction responsive ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#723)
- [x] **Config mic-test result row clips long errors** — fixed `h-7 overflow-hidden`; allow wrap/grow ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#723)
- [x] **Config dirty/seed `JSON.stringify` churn** — 4-5 full serializations per keystroke; memoize/compare smarter ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#723)
- [x] **VoiceTest reverse-scan derivations + index keys** — `[...events].reverse().find` per change and index-based timeline keys; single backward pass + stable ids ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#723)
- [x] **SessionExpiredModal actions don't stack on narrow** — add `flex-col sm:flex-row`; lock body scroll + inert background while blocking ([`SessionExpiredModal.tsx`](webui/frontend/src/components/SessionExpiredModal.tsx))  ✅ (#723)
- [x] **Dead `pattern-isometric` class on Login** — referenced but undefined; define it or remove the dead class ([`LoginPage.tsx`](webui/frontend/src/pages/LoginPage.tsx))  ✅ (#723)

---

## Backlog — round 4 (from 2026-06-20 diversified audit: backend + docs + visual)

The backend hadn't been critiqued this session; this pass found real bugs there
plus stale docs. Fix backend correctness first.

### Backend — correctness/robustness (10/10)

- [x] **Config PUT shallow-merges → data loss** — `PUT /api/v1/config` does `cfg.update(filtered_data)`, so a client sending one nested subkey replaces the whole top-level block (e.g. `{"advisors":{"providers":{"model":"x"}}}` drops `api_key`/`base_url`). Deep-merge allowed keys recursively ([`web/routes/core.py`](src/chatty_commander/web/routes/core.py))  ✅ (#726)
- [x] **GET/PUT /config leak internals + 500** — both re-raise `HTTPException(500, detail=str(err))`, violating "degrade, never 500" + "no internals in client strings". GET should 200 with honest empty; PUT a generic message + log detail ([`web/routes/core.py`](src/chatty_commander/web/routes/core.py))  ✅ (#726)
- [x] **SqliteRevocationStore writes on read + leaks connections** — `is_revoked` does a `DELETE`+`commit` (serializes auth under a write lock); a new store is built per `create_app` with no `close()`. Don't write in `is_revoked`; wire `close()` ([`web/revocation.py`](src/chatty_commander/web/revocation.py), [`web/server.py`](src/chatty_commander/web/server.py))  ✅ (#726)
- [x] **dograh track/untrack not scope-gated** — state-changing POSTs lack `require_scope`; any valid key can start/stop the poller ([`web/routes/dograh.py`](src/chatty_commander/web/routes/dograh.py))  ✅ (#726)
- [x] **models upload/delete not role-gated + unbounded upload** — destructive endpoints behind only the coarse key middleware; gate behind `require_role("admin")`; stream upload with a size cap (currently whole-file `await file.read()`) ([`web/routes/models.py`](src/chatty_commander/web/routes/models.py))  ✅ (#726)
- [x] **get_dograh_workflows can 500** — `int(wf["id"])` outside the try/except 500s on a non-numeric id; guard malformed rows ([`web/routes/dograh.py`](src/chatty_commander/web/routes/dograh.py))  ✅ (#726)
- [x] **AuthMiddleware 401 uses a non-standard body** — differs from the `{error,code,details,request_id}` envelope; emit the same shape ([`web/middleware/auth.py`](src/chatty_commander/web/middleware/auth.py))  ✅ (#726)
- [x] **ws `on_message` callback unguarded** — a raising `on_message` tears down the /ws connection; wrap it ([`web/routes/ws.py`](src/chatty_commander/web/routes/ws.py))  ✅ (#726)
- [x] **change_state maps all errors to 400 + str(err)** — don't return 400+internals for internal failures ([`web/routes/core.py`](src/chatty_commander/web/routes/core.py))  ✅ (#726)
- [x] **Rate limiter disabled by ambient `PYTEST_CURRENT_TEST`** — gate on an explicit opt-out ([`web/routes/core.py`](src/chatty_commander/web/routes/core.py))  ✅ (#726)

### Docs — accuracy (8/8)

- [x] **docs/API.md is an unrendered template** — literal `{datetime.now()...}` + `{{...}}`; regenerate via the builder, fix the GET /config example + document `/api/v1/auth/*` + `chatty-commander --web` ([`docs/API.md`](docs/API.md))  ✅ (#726)
- [x] **ARCHITECTURE.md theme list + facts wrong** — real themes light/dark/corporate/business/emerald/nord; rate-limit 100→60; add AuthZ rotation/revocation + dograh WS; vitest no longer "incomplete" ([`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md))  ✅ (#726)
- [x] **README stale** — "vitest unconfigured" is false; Web-dashboard row omits Commands table/bulk-ops + theme switcher ([`README.md`](README.md))  ✅ (#726)
- [x] **WEBUI_ISSUES.md stale** — 5 pages + "Partial/placeholder" caveats now resolved; app has 7 routed pages ([`docs/developer/WEBUI_ISSUES.md`](docs/developer/WEBUI_ISSUES.md))  ✅ (#726)
- [x] **FEATURE_STATUS.md page count stale** — "Five SPA pages" → seven; note ErrorBoundary/SessionExpiredModal/theme persistence ([`FEATURE_STATUS.md`](FEATURE_STATUS.md))  ✅ (#726)
- [x] **Guided tour references a deleted screenshot** — `tour-06-theme-synthwave.png` → `tour-06-theme-emerald.png` ([`docs/user-guide/00_GUIDED_TOUR.md`](docs/user-guide/00_GUIDED_TOUR.md))  ✅ (#726)
- [x] **STRUCTURE.md root layout wrong** — references `config/` + `deploy/` dirs that don't exist ([`docs/developer/STRUCTURE.md`](docs/developer/STRUCTURE.md))  ✅ (#726)
- [x] **CONTRIBUTING.md omits the unit suite** — add `npm run test` (vitest) ([`CONTRIBUTING.md`](CONTRIBUTING.md))  ✅ (#726)

### Visual (4/4)

- [x] **VoiceTest sidebar brand inconsistent (recurring)** — still "Chatty / Voice Commander" instead of the shared Logo; root-cause + use `Logo` ([`VoiceTestPage.tsx`](webui/frontend/src/pages/VoiceTestPage.tsx))  ✅ (#726)
- [x] **Radial gauges render flat grey** — no proportional themed fill; color-code by load threshold ([`DashboardPage.tsx`](webui/frontend/src/pages/DashboardPage.tsx))  ✅ (#726)
- [x] **Audio Input vs Output "Test" buttons different colors** — unify ([`ConfigurationPage.tsx`](webui/frontend/src/pages/ConfigurationPage.tsx))  ✅ (#726)
- [x] **Default seed data looks broken** — canonical `commands.png` shows commands named "0,1,2,3 / NO ACTION"; seed real named default commands ([`default_config`](src/chatty_commander/app/default_config.py))  ✅ (#726)

---

## Backlog — round 5 (from 2026-06-20 audit of CLI / voice / advisors)

Reviewed the previously-uncritiqued backend subsystems. Found real security +
correctness bugs. Fix security/correctness first; many P2 robustness items can
land incrementally.

### Security / correctness (9/9)

- [x] **`_execute_url` SSRF TOCTOU** — validates with `is_safe_url(url)` then fetches the original hostname (DNS-rebinding bypass `is_safe_url`'s own docstring warns about); switch to the repo's `resolve_safe_url()` + connect to the pinned IP with the original Host/SNI ([`app/command_executor.py`](src/chatty_commander/app/command_executor.py))  ✅ (#728)
- [x] **`SWITCH_MODE:` state injection** — LLM output `SWITCH_MODE:<target>`/`target_mode` is passed to `StateManager.change_state()` with no allowlist, so a prompt-injected reply (e.g. via browser_analyst web content) can drive any mode; validate against `{idle, computer, chatty}` ([`advisors/service.py`](src/chatty_commander/advisors/service.py), [`ai/intelligence_core.py`](src/chatty_commander/ai/intelligence_core.py))  ✅ (#728)
- [x] **dograh_place_call no phone validation** — LLM-supplied `phone_number`/`workflow_id` dialed with no E.164/type check (toll-fraud once the opt-in tool is enabled); validate before `initiate_call` ([`advisors/tools/dograh_call.py`](src/chatty_commander/advisors/tools/dograh_call.py))  ✅ (#728)
- [x] **`is_available()` has paid/slow side effects** — `OpenAIBackend.is_available` fires a billed `chat.completions.create`; Ollama can trigger a 300s model *pull*; both run during `LLMManager` construction. Make availability a cheap credential/reachability check; never auto-pull during selection ([`llm/backends.py`](src/chatty_commander/llm/backends.py), [`llm/manager.py`](src/chatty_commander/llm/manager.py))  ✅ (#728)
- [x] **Ollama generate path skips URL validation** — `is_safe_url` runs only in `is_available()` (cacheable/skippable), not before the `/api/generate`/`/api/pull` POSTs; validate immediately before each outbound request ([`llm/backends.py`](src/chatty_commander/llm/backends.py))  ✅ (#728)
- [x] **`transcription._record_audio` ZeroDivisionError** — RMS over a zero-length chunk (PyAudio can return `b""`) divides by zero, breaking the record loop; `continue` on empty chunk (same in `enhanced_processor._energy_based_vad`) ([`voice/transcription.py`](src/chatty_commander/voice/transcription.py))  ✅ (#728)
- [x] **wake-word detection race + unbounded threads** — `_on_wake_word_detected` does a non-atomic check-then-set on `_processing` and spawns an untracked daemon thread per detection; two rapid wake words spawn two recorders contending for the mic. Guard with a lock; set the flag inside it ([`voice/pipeline.py`](src/chatty_commander/voice/pipeline.py))  ✅ (#728)
- [x] **wakeword `stop_listening` use-after-free** — sets `_running=False` then `join(timeout=1)`, but the loop can be blocked in a >1s `stream.read`; on timeout the stream is closed while the loop may still read it. Close under a lock / have the loop re-check `_running` ([`voice/wakeword.py`](src/chatty_commander/voice/wakeword.py))  ✅ (#728)
- [x] **`service._generate_llm_response` reads `current_mode` off a dict via `getattr`** → always `"chatty"`; use `self.config.get("current_mode", "chatty")` ([`advisors/service.py`](src/chatty_commander/advisors/service.py))  ✅ (#728)

### Robustness / quality (12/12)

- [x] **enhanced_processor numpy import unguarded** — top-level `import numpy` crashes the module if numpy is absent (siblings guard it); wrap it ([`voice/enhanced_processor.py`](src/chatty_commander/voice/enhanced_processor.py))  ✅ (#728)
- [x] **api_docs builder emits template literals** — `generate_markdown_docs()` returns a plain string with `{datetime.now()}` + `{{}}`; make the date header an f-string and single-brace the body (don't `.format()` the whole doc) ([`cli/api_docs/builder.py`](src/chatty_commander/cli/api_docs/builder.py))  ✅ (#728)
- [x] **recurring event-loop test flake** — `test_broadcast_and_on_hooks_use_event_loop` ("Event loop is closed" under some orderings); make the broadcast path tolerate a missing/closed loop and isolate the test ([`web/web_mode.py`](src/chatty_commander/web/web_mode.py), [`tests/unit/test_web_mode_unit.py`](tests/unit/test_web_mode_unit.py))  ✅ (#728)
- [x] **`save_config` returns None on failure** — callers (`set_model_action`, `_update_general_setting`) believe a write succeeded when the disk is full/read-only; return a bool/raise ([`app/config.py`](src/chatty_commander/app/config.py))  ✅ (#729)
- [x] **keypress presses unmapped literal strings** — a `keys:"take_screenshot"` (no `+`, not a list) reaches `pyautogui.press("take_screenshot")` (invalid); validate against KEYBOARD_KEYS / resolve macros, `report_error` on unknown ([`app/command_executor.py`](src/chatty_commander/app/command_executor.py))  ✅ (#728)
- [x] **memory/context unbounded on disk** — `MemoryStore` is append-only JSONL (grows forever, full replay on load); `ContextManager` never expires + re-serializes all contexts per message; compact + debounce ([`advisors/memory.py`](src/chatty_commander/advisors/memory.py), [`advisors/context.py`](src/chatty_commander/advisors/context.py))  ✅ (#729)
- [x] **voice_test transcription blocks the event loop** — `finish_audio` runs sync Whisper inference inside the WS receive loop; `await asyncio.to_thread(...)` ([`web/routes/voice_test*`](src/chatty_commander/web/routes/voice.py))  ✅ (#729)
- [x] **conversation_engine substring intent matching** — `"do" in text` / `"hi" in text` mis-fire on "window"/"this"; mirror the word-boundary regex from intelligence_core ([`advisors/conversation_engine.py`](src/chatty_commander/advisors/conversation_engine.py))  ✅ (#729)
- [x] **dual drifting command matchers** — `pipeline` and `voice_test_pipeline` have separate word-boundary matchers/keyword tables that already diverged (play_music); extract one shared matcher ([`voice/pipeline.py`](src/chatty_commander/voice/pipeline.py))  ✅ (#729)
- [x] **CLI `--advisors` dead flag + triple web-override + `not args.no_auth`** — `args.advisors` referenced but never defined; web host/port/auth applied in 3 places and `--web` recomputes `auth_enabled = not args.no_auth` (ignores config `auth_enabled:false`); consolidate ([`cli/cli.py`](src/chatty_commander/cli/cli.py), [`cli/main.py`](src/chatty_commander/cli/main.py))  ✅ (#729)
- [x] **CLI port validation + `run_cli_mode` finally sys.exit(0)** — port only checked `<1024` under `--web` (no upper bound); `finally: sys.exit(0)` always reports success + swallows errors; validate `1..65535`, return instead of exit ([`cli/cli.py`](src/chatty_commander/cli/cli.py))  ✅ (#729)
- [x] **config.py + main.py merge cruft** — duplicated `_load_config`/`from_dict`/`_build_model_actions` blocks; stale `run_gui_mode` fallback in main.py; dedupe + delegate ([`app/config.py`](src/chatty_commander/app/config.py), [`cli/main.py`](src/chatty_commander/cli/main.py))  ✅ (#729)

---

## Backlog — round 6 (from 2026-06-20 audit of middleware / metrics / avatars / GUI)

The last-uncritiqued surfaces still had real bugs. Most of the reviewed code was
confirmed solid (trusted-proxy handling, security headers, agents/audio/version
routes, rate-limiter pruning) — these are the genuine issues.

### Security (4/4)

- [x] **`/avatar/*` routes bypass auth** — `AuthMiddleware` only gates `path.startswith("/api/")`, but the avatar routes live at `/avatar/...`; in particular **`/avatar/launch` spawns a host subprocess unauthenticated** (local DoS / process spawn). Gate `/avatar/launch` (and the other state-changing avatar routes) behind auth + add an idempotency/single-instance guard — without breaking the avatar client that connects to `/avatar/ws` ([`web/routes/avatar_api.py`](src/chatty_commander/web/routes/avatar_api.py), [`web/middleware/auth.py`](src/chatty_commander/web/middleware/auth.py))  ✅ (#731)
- [x] **`/api/preferences` + `/api/restore` dead allow-list** — `if k in ALLOWED_PREF_KEYS or True:` always passes, so any config key (`auth`, `web_server`) can be overwritten + persisted; drop the `or True`, actually filter ([`web/routes/system.py`](src/chatty_commander/web/routes/system.py))  ✅ (#731)
- [x] **Rate-limit default effectively off** — `requests_per_minute=10000`; lower to a sane default (e.g. 600) and/or make it `web_server.rate_limit_rpm`-configurable ([`web/web_mode.py`](src/chatty_commander/web/web_mode.py))  ✅ (#731)
- [x] **`apply_cors` wildcard in no-auth** — `allow_origins=["*"]` when `no_auth=True` (credentials correctly dropped, but still readable by any site); default to a localhost allowlist like web_mode already does ([`web/auth.py`](src/chatty_commander/web/auth.py))  ✅ (#731)

### Metrics correctness (4/4)

- [x] **obs/metrics readers race the writers** — `Counter/Gauge/Histogram` readers iterate `_values`/`_counts` without the lock while request threads mutate under it → "dictionary changed size during iteration" 500 on a concurrent `/metrics` scrape; snapshot under the lock ([`obs/metrics.py`](src/chatty_commander/obs/metrics.py))  ✅ (#731)
- [x] **Prometheus `+Inf` histogram bucket invalid** — `+Inf` is emitted as `counts[-1]` (only over-all-edges count), not the cumulative total, producing a non-monotonic histogram that breaks Prometheus parsing; emit the running total and make finite buckets cumulative ([`obs/metrics.py`](src/chatty_commander/obs/metrics.py))  ✅ (#731)
- [x] **request-duration histogram always `route:"unknown"`** — the `Timer` closes before the route is resolved; resolve the route after `call_next` and observe with the real label ([`obs/metrics.py`](src/chatty_commander/obs/metrics.py))  ✅ (#731)
- [x] **metrics middleware no try/finally** — a raising handler skips the request counter (undercounts errors) and breaks the "metrics never affect the app path" guarantee; wrap in try/finally ([`obs/metrics.py`](src/chatty_commander/obs/metrics.py))  ✅ (#731)

### Avatar / GUI robustness (5/5)

- [x] **avatar_ws connection list mutated cross-thread** — `active_connections` (a list) is mutated from the loop and from `broadcast_state_change` invoked off-thread via `asyncio.run`; guard with a lock or marshal onto the server loop ([`web/routes/avatar_ws.py`](src/chatty_commander/web/routes/avatar_ws.py))  ✅ (#731)
- [x] **thinking_state broadcasts via `asyncio.run` per call** — spins a fresh loop per state change (sockets bound to the server loop → dropped sends); capture the server loop + `run_coroutine_threadsafe`, and make `set_agent_state` auto-register atomic ([`avatars/thinking_state.py`](src/chatty_commander/avatars/thinking_state.py))  ✅ (#731)
- [x] **avatar_ws audio queue bound to import-time loop** — `asyncio.Queue()` created at import may belong to a closed/other loop; create it lazily in the running loop ([`web/routes/avatar_ws.py`](src/chatty_commander/web/routes/avatar_ws.py))  ✅ (#731)
- [x] **web_mode `_on_state_change` + duplicate asset mount** — `_on_state_change` builds a non-running loop (silent drop + leak); route it through `_schedule_broadcast`; remove the duplicated `app.mount("/assets", ...)` block ([`web/web_mode.py`](src/chatty_commander/web/web_mode.py))  ✅ (#731)
- [x] **GUI degrade-not-crash** — `pyqt5_avatar` references `pyqtSignal` at class-definition when PyQt5 is absent → `NameError` on import (should degrade); `tray_popup` resolves `icon.png` from CWD (silent miss) + leaks the webview thread on quit ([`gui/pyqt5_avatar.py`](src/chatty_commander/gui/pyqt5_avatar.py), [`gui/tray_popup.py`](src/chatty_commander/gui/tray_popup.py))  ✅ (#731)

---

## Backlog — round 7 (from 2026-06-20 audit of CI/build + test-infra + security verification)

The security-verification pass found two of the recent fixes were INCOMPLETE
(the avatar-auth and preferences-allowlist holes have twins in other files).
Fix those first.

### Security — incomplete fixes / new holes (5/6)

- [x] **`PUT /avatar/config` still bypasses auth** — same hole as the just-fixed `/avatar/launch`, but in `avatar_settings.py` (registered outside `/api/`, persists config); gate it behind `require_role` ✅ (#733 — gated with `require_role("user")`) ([`web/routes/avatar_settings.py`](src/chatty_commander/web/routes/avatar_settings.py))
- [x] **Second UNFILTERED `PUT /api/preferences` shadows the fix** — `preferences.py` registers a `PreferencesModel(extra="allow")` handler with `prefs.update(updates)` BEFORE the `ALLOWED_PREF_KEYS`-filtered one in `system.py`, so FastAPI dispatches to the unfiltered one → arbitrary config write still open + my round-6 fix is dead code on the real path; apply the allow-list in `preferences.py` (or remove the duplicate) ✅ (#733 — added `ALLOWED_PREF_KEYS` filter on the winning handler) ([`web/routes/preferences.py`](src/chatty_commander/web/routes/preferences.py))
- [x] **dograh phone validation incomplete** — the E.164 guard is only in the LLM tool (`advisors/tools/dograh_call.py`), not the config/wake-word path (`command_executor._validate_dograh_call_params`) nor `DograhClient.initiate_call`; move the E.164 check into `DograhClient.initiate_call` so both paths are covered ✅ (#733 — `DograhValidationError` + E.164/workflow_id validation in `initiate_call`) ([`integrations/dograh_client.py`](src/chatty_commander/integrations/dograh_client.py))
- [x] **WebSocket endpoints unauthenticated** — `/ws`, `/avatar/ws`, `/ws/voice-test` bypass `AuthMiddleware` (BaseHTTPMiddleware can't see WS scope); `/ws/voice-test` is state-changing. Add an explicit token/key check in the WS accept handlers (gated so no-auth stays open) ✅ (#733 — `authorize_websocket` + `?token=` JWT, gated on `is_auth_active()`) ([`web/routes/ws.py`](src/chatty_commander/web/routes/ws.py), [`web/routes/voice_test.py`](src/chatty_commander/web/routes/voice_test.py))
- [ ] **Auth middleware is a prefix-allowlist (root cause)** — only `/api/*` is protected; every non-`/api/` route silently bypasses the legacy X-API-Key gate. ⚠️ **Exposure mitigated, literal rewrite deferred (#734):** every genuinely state-changing non-`/api/` route is now individually gated — `/avatar/launch` + `PUT /avatar/config` via `require_role`, `/ws` + `/avatar/ws` + `/ws/voice-test` via `authorize_websocket`, `/bridge/event` via its own `X-Bridge-Token`; `/avatar/animation/choose` is a stateless classifier (no persistence). A blanket default-deny middleware rewrite was rejected as net-negative: it would double-gate `/bridge/event`'s bespoke token auth and risk breaking SPA/static serving, for no marginal security gain. Revisit only if a new mutating non-`/api/` route lands without its own gate ([`web/middleware/auth.py`](src/chatty_commander/web/middleware/auth.py))
- [x] **`providers.health_check` does a billable call** — the no-billing fix only touched `llm/backends.is_available`; `advisors/providers.health_check` still does a real `generate("Test")`; make it a cheap local check ✅ (#733 — cheap local readiness check, no billable generate) ([`advisors/providers.py`](src/chatty_commander/advisors/providers.py))

### Test infrastructure (3/4)

- [x] **Two competing pytest configs** — `pytest.ini` overrides `[tool.pytest.ini_options]`, dropping `--strict-markers`/`--strict-config` and re-enabling `--cov` (vs the documented `-q --no-cov`), and only 4 of the 30 markers are registered; consolidate into one ✅ (#733 — deleted `pytest.ini`, merged `pythonpath`/`asyncio_mode`/`filterwarnings` into `pyproject.toml`) ([`pyproject.toml`](pyproject.toml))
- [x] **Module-level `sys.modules` stubs leak** — `test_cli_features.py` + `test_wakeword_comprehensive.py` install fake openwakeword/pyaudio at import and never remove them (order-dependence); move to autouse `monkeypatch.setitem` like the rest of the suite ✅ (#733) ([`tests/`](tests/))
- [ ] **No random test ordering** — order-dependence is hidden (module-global stores + the leaking stubs); add `pytest-randomly` to surface coupling ([`pyproject.toml`](pyproject.toml))
- [x] **Racy sleep-based WS tests** — `test_websocket_routes.py` gates heartbeat assertions on real `time.sleep`; flaky under load. Poll-with-deadline / deterministic scheduling ✅ (#733 — `_wait_until` poll helper) ([`tests/unit/test_websocket_routes.py`](tests/unit/test_websocket_routes.py))

### CI / build / packaging (4/5)

- [x] **`screenshots.yml` double-starts the server** — it manually starts on :8100 while Playwright's `webServer` (reuseExistingServer=false in CI) also binds :8100 → port conflict; drop the manual step or set reuse ✅ (#733 — removed manual server start; Playwright `webServer` owns :8100) ([`.github/workflows/screenshots.yml`](.github/workflows/screenshots.yml))
- [x] **perf-smoke / screenshots don't disable the rate limiter** — the live 600/min limiter can 429 a k6 smoke / screenshot burst; export `CHATTY_DISABLE_RATE_LIMIT=1` on the server-start step ✅ (#733) ([`.github/workflows/perf-smoke.yml`](.github/workflows/perf-smoke.yml), [`.github/workflows/screenshots.yml`](.github/workflows/screenshots.yml))
- [x] **No `[build-system]` in pyproject** — `python -m build` / plain `pip wheel .` fell back to setuptools; add an explicit build backend ✅ (#734 — `[build-system]` hatchling + `[tool.hatch.build.targets.wheel]` for the src-layout; `uv build` produces wheel+sdist) ([`pyproject.toml`](pyproject.toml))
- [~] **Two frontend lockfiles + version drift** — version drift RECONCILED ✅ (#734 — `pyproject` `0.2.0`→`0.5.0`, `package.json` `1.0.0`→`0.5.0`, removed stale `src/chatty_commander.egg-info` that shadowed package metadata at `0.2.0`, and made every runtime version source read `__version__` single-source-of-truth: `core.py`/`web_mode.py`/`version.py`/`api_docs.builder`). **Still open:** the two committed lockfiles (`package-lock.json` for npm jobs + `pnpm-lock.yaml` for the pnpm e2e job) — consolidating to one tool needs a CI-workflow audit + a green CI run to validate, so it's left as a deliberate decision ([`webui/frontend`](webui/frontend), [`pyproject.toml`](pyproject.toml))
- [x] **`@playwright/test` floor `^1.40.0`** drifts from the resolved 1.58.2 / Python `playwright>=1.58.0`; bump the floor ✅ (#733 — floor bumped to `^1.58.0`) ([`webui/frontend/package.json`](webui/frontend/package.json))

---

## Done (recent)

2026-06-11 (continued):

- ✅ Optional **Edge TTS** backend (keyless, neural; `synthesize_to_file` helper) behind the existing `TTSBackend` interface; pyttsx3 stays default (#689)
- ✅ dograh call-state poller **auto-starts** on `initiate_call` (#688)
- ✅ **AuthZ phase 1** — token refresh + jti revocation (#690)

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
