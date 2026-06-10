# CLAUDE.md

ChattyCommander: local-first voice assistant — wake words → actions (keypress/URL/system/voice-call). Python 3.11 FastAPI backend + React webui + CLI.

## Commands

```bash
uv sync                                  # install (uv-managed venv)
uv run pytest -q --no-cov                # full Python suite (~900 tests, ~15s, must stay green)
uv run ruff check . && uv run mypy src   # both gate CI (currently clean)
cd webui/frontend && npm run test        # vitest unit tests
cd webui/frontend && npm run build       # production build (must pass)
npx playwright test tests/e2e/guided_tour.spec.ts  # regenerates docs/screenshots/tour-*.png
uv run chatty-commander --web --no-auth  # dev server (refuses with CHATTY_ENV=production)
```

## Layout

- `src/chatty_commander/` — `app/` (config, state machine, command_executor, orchestrator), `web/` (FastAPI; routes in `web/routes/`, factories in `server.py` + `web_mode.py` sharing `register_shared_routers()`), `cli/`, `advisors/` (LLM agents + tools), `integrations/` (dograh client), `voice/`, `utils/`
- `webui/frontend/` — React + Vite + DaisyUI; e2e in `tests/e2e/`
- Tests in `tests/` (pytest config in `pyproject.toml`)

## Conventions

- Conventional commits; commit per logical group; suite must be green before push (commits go straight to `main`)
- New API surface: one file in `web/routes/` exposing `include_X_routes`/`register_X_routes`, registered via `register_shared_routers()` in `web/server.py` so BOTH app factories get it
- Endpoints degrade gracefully (missing hardware/integration → 200 with honest empty state, never 500); errors use the `{error, code, details, request_id}` shape from `web/errors.py`
- Client-visible strings/log lines never include internal URLs (see `DograhHTTPError`); distinct failure branches use distinct, test-pinned log phrases
- `no_auth=True` is dev-only and structurally refused in production (`ensure_no_auth_allowed`)

## Source of truth for "what's left"

- `ROADMAP.md` — canonical nested checklist (P0/P1/P2 + security backlog from closed bot PRs #617-#649)
- `FEATURE_STATUS.md` — evidence-table feature audit (re-verify rows before acting; dated 2026-06-10)
- History note: main was reset to a healthy baseline at `3ac5ea05` (June 2026) after a bot-PR flood broke it; don't trust pre-reset branches/PRs.
