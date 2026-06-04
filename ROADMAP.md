# ChattyCommander Roadmap

A tiered, checkbox-driven TODO list. Tiers are about urgency, not size:

| Tier | Meaning | When |
|------|---------|------|
| **P0** | Must land before this branch merges to `main` | This sprint |
| **P1** | Quality polish — should land within the dograh phase 1 window | Next sprint |
| **P2** | Phase 2 — WebRTC bridge, deeper integration | Q3 |
| **P3** | Phase 3 / horizon — UI consolidation, future direction | Q4+ |

See also: [`docs/developer/PRODUCTION_READINESS_ROADMAP.md`](docs/developer/PRODUCTION_READINESS_ROADMAP.md) for the broader (non-dograh) production-readiness backlog.

---

## P0 — Blockers for `feat/dograh-phase-1` → `main`

### Security

- [x] **HIGH — `server.create_app()` is missing `AuthMiddleware`** ([`src/chatty_commander/web/server.py:113`](src/chatty_commander/web/server.py))
  Anyone reaching a server started via `server.create_app` can hit `/api/v1/dograh/status` and `/api/v1/dograh/workflows` with zero auth. `web_mode.WebModeHandler` is fine because it adds the middleware. Fix: attach `AuthMiddleware` in `create_app` or refuse to bind to a non-loopback interface.

- [x] **MED — Raw dograh `/health` body passthrough** ([`src/chatty_commander/web/routes/dograh.py:74`](src/chatty_commander/web/routes/dograh.py))
  The route returns `DograhStatus(health=payload)` verbatim. Today that's just `status`/`version`/`deployment_mode` (mild version disclosure). When dograh adds queue depths / DB info / internal URLs in a future release, those leak straight to any UI caller. Project an allowlist (`status`, `version` only).

- [x] **MED — `DograhHTTPError` leaks internal URL into client-visible `reason`** ([`src/chatty_commander/integrations/dograh_client.py:41`](src/chatty_commander/integrations/dograh_client.py))
  Exception message is `"{method} {url} -> {status}: {detail}"`. The route swallows it into `reason=f"unreachable: {e}"`, exposing the dograh hostname. Return a generic `"unreachable"` from the route; log details server-side.

- [ ] **MED — Rotate the secrets currently in on-disk `.env`** (`.env:29`, `.env:35`)
  `DOGRAH_OSS_JWT_SECRET` (64-hex) and `DOGRAH_API_KEY` (`dgr_…`) are live values, file mode 0664. Git history confirmed clean (no commit ever contained them), but local shell access = key access. Rotate both, `chmod 600 .env`.

### Correctness

- [x] **Silent dual-registration in `cli/main.py`** ([`src/chatty_commander/cli/main.py:524`](src/chatty_commander/cli/main.py))
  Today there's both a hard-coded short-circuit (added in `48017506` to fix the original bug) AND a `register_dograh_subparser` call in `create_parser()`. Pick one. The parser path is cleaner — remove the short-circuit once we verify `parse_known_args()` doesn't trigger heavy init for `dograh` subcommands.

---

## P1 — Phase 1 polish (before declaring dograh integration done)

### Code hygiene

- [x] **Delete the shadow `src/chatty_commander/tools/` package**
  This is the trap that caused the original `..tools.X` → wrong-package bug (fixed in `69a124d0`). The package currently only holds incidental CLI utilities. Move them under `advisors/tools/` or `cli/` and delete the directory, eliminating the import-resolution footgun.

- [x] **Unify `web_mode._create_app` vs `server.create_app`**
  Both factories exist and both wire dograh, but they diverge in pattern (explicit `include_router` vs `_include_optional` loop). Consolidate to one — ideally `web_mode.py` since it's the production path. `server.py` should either delegate to it or be deleted.

- [x] **Orchestrator `advisor_sink` is accepted but never used** ([`src/chatty_commander/app/orchestrator.py:181`](src/chatty_commander/app/orchestrator.py))
  Either route advisor messages through it (so `--orchestrate --enable-discord-bridge --advisors` actually works), or mark as `TODO` and stop pretending to accept it.

- [x] **Seed script "legacy" stdout mode still prints raw API key** ([`scripts/seed_dograh.py:103`](scripts/seed_dograh.py))
  `bbb550e5` fixed CI by adding `--output`, but interactive `python scripts/seed_dograh.py` (no flags) still echoes the live key into terminal scrollback. Either deprecate stdout mode or require `--print-secret` to opt in.

- [x] **`dograh_call.py` warning logs full `DograhHTTPError`** ([`src/chatty_commander/advisors/tools/dograh_call.py:60`](src/chatty_commander/advisors/tools/dograh_call.py))
  Same shape as the route leak — includes method + URL. Log `e.status_code` and `e.detail` separately.

### Test coverage

- [x] **CLI error branches** — `cli/dograh_cli.py:124-129` (DograhError + generic Exception in dispatcher), `:133-134` (unknown op exit code 2), `:146-147` + `:190-191` (`--json` output for list/runs). All user-facing surfaces.

- [x] **`_execute_dograh_call` generic Exception path** — `command_executor.py:370-372`. Different `reason` string from `DograhError`; operators grep logs by phrase.

### UX / Documentation

- [x] **README has no mention of dograh.** Add a short "Optional: dograh integration" section pointing at the docker overlay + `.env.example` block.

- [ ] **Author a real telephony workflow in dograh's UI** and document the steps (user action).
- [ ] **Configure a Twilio/Vonage provider** so `dograh_call` returns success instead of `telephony_not_configured` (user action).
- [ ] **Wire dograh's LLM / STT / TTS providers for self-hosted use**
  The dograh OSS image ships pointing all three at a hosted "dograh" provider that requires their cloud account. To run an end-to-end voice call locally (no Twilio needed — dograh ships a `smallwebrtc` browser-call mode), we must replace those with self-hosted or BYO-credential providers. Options: (a) OpenAI keys for all three, simplest; (b) stand up the optional Speaches stack (local Whisper + Kokoro TTS) and point dograh at it via `PUT /api/v1/user/configurations/user`. See `webui/frontend/tests/e2e/dograh/dograh_webcall_loopback.spec.ts` and `docs/screenshots/dograh/03-webcall-loopback.png` for the captured "blocked at LLM config" state.
- [x] **Rebase `feat/dograh-phase-1` onto `main`** — done via merge `454f3873` (97-commit divergence made a literal rebase impractical; origin/main fully integrated, suite green).

---

## P2 — Phase 2: WebRTC audio bridge

- [ ] Bring CC's wake-word detector and dograh's pipecat audio pipeline onto a shared audio stream so a wake-word can interrupt and hand off to an in-progress dograh call.
- [ ] Bidirectional state: dograh call state (`ringing`/`in-call`/`ended`) reflected in CC's `StateManager`; CC's `chatty`/`computer` mode published to dograh's session metadata.
- [ ] E2E test: wake-word → dograh call → live audio → call end → CC returns to `idle`.

---

## P3 — Phase 3: UI consolidation

- [ ] Decide on direction: CC's React app embedded in dograh's Next.js dashboard, dograh's workflow editor embedded in CC, or a single new shell hosting both.
- [ ] Single sign-on between the two services (currently CC uses session cookies, dograh uses X-API-Key + JWT).
- [ ] Migrate the dograh status card from a polling React Query to a WebSocket push from CC's existing `/ws` channel.

---

## Done (recent)

- ✅ Dograh OSS docker overlay (`docker-compose.dograh.yml`) — 5-service stack on remapped ports, opt-in via `COMPOSE_FILE`.
- ✅ End-to-end Python client (`integrations/dograh_client.py`) with `X-API-Key` auth, structured errors, 99% test coverage.
- ✅ `cc dograh {health,list,call,show,runs,run-info}` CLI subcommand group.
- ✅ Wake-word → `dograh_call` action wired into `CommandExecutor`.
- ✅ Advisor LLM tool (`dograh_place_call`) wired into `CompletionProvider`.
- ✅ FastAPI routes `/api/v1/dograh/{status,workflows}` with graceful degradation.
- ✅ React `DograhStatusCard` on the dashboard with online + offline states (Playwright screenshots captured).
- ✅ CI workflow (`.github/workflows/dograh-integration.yml`) with secret masking and seed bootstrap.
- ✅ Two latent silent-registration bugs caught and fixed (`69a124d0` advisors tools import path, `48017506` CLI subcommand dispatch).
