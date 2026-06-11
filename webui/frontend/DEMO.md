# ChattyCommander Web UI — Static Demo

A **fully static, no-backend, no-API-keys** build of the ChattyCommander web UI.
It can be deployed to GitHub Pages or any static host (no Node, no Python, no
running server). All API responses are pre-recorded fixtures and the WebSocket
is faked, so the dashboard renders live-looking data with nothing behind it.

The demo is **opt-in behind a build-time flag** (`VITE_DEMO`). The normal build
(`npm run build`) is completely unchanged — none of the demo code is referenced
or bundled when the flag is unset (it is dynamically imported behind the guard
and tree-shaken out).

## What it is / what's stubbed

When `VITE_DEMO=1`, `src/index.tsx` dynamically imports and runs
`src/demo/installDemoMocks.ts` **before** the app renders. That shim:

- **`window.fetch` is monkeypatched.** Any `/health` or `/api/...` GET is served
  from a bundled fixture (`src/demo/fixtures/*.json`, keyed by path in
  `src/demo/fixtures.ts`). Unrecorded GETs return `{}` with a `console.warn`.
  POST/PUT/DELETE return a friendly canned `{ status: "ok", demo: true }` so the
  UI's optimistic flows (command execute, config save) don't error. **No network
  request ever leaves the page.**
- **`window.WebSocket` is replaced** with `FakeWebSocket`
  (`src/demo/FakeWebSocket.ts`). It never connects — it immediately reports
  `OPEN` (so the dashboard badge shows **Connected**, not stuck "Reconnecting…")
  and emits a few scripted frames:
  - on `/ws`: `{type:'telemetry', data:{cpu,memory}}` frames on an interval, so
    the live CPU/Memory stats and the performance chart show movement;
  - on `/ws/voice-test`: a short scripted dry-run pipeline (listening → wakeword
    → transcript → match → dry-run action) for the Voice Test page.
- **`DemoBanner`** (`src/demo/DemoBanner.tsx`) is mounted at the app root: a
  prominent, dismissible notice (dismissal persisted in `localStorage`).

> **Caveat — the WebSocket is faked.** The demo does **not** replay a real
> recorded socket session; `FakeWebSocket` synthesizes plausible frames
> client-side. Live voice capture, real AI/advisor responses, and the Dograh
> voice-call integration are **not** functional in the demo (Dograh correctly
> shows "Offline"). Those require a local install with the real backend.

## Build it

```bash
cd webui/frontend
npm install            # first time only
npm run build:demo     # -> webui/frontend/demo-dist/
```

`build:demo` runs `vite build --mode demo --outDir demo-dist`. The `--mode demo`
flag makes Vite auto-load `.env.demo` (which sets `VITE_DEMO=1`); the build is
still a normal production/minified build. Equivalent manual invocation:

```bash
VITE_DEMO=1 npm run build -- --outDir demo-dist
```

The output (`demo-dist/`) is **gitignored** (see `webui/frontend/.gitignore`) —
commit the **source + fixtures**, not the built artifact.

## Preview it locally (no backend!)

```bash
python3 -m http.server -d webui/frontend/demo-dist 8199
# then open http://localhost:8199/
```

(Any static file server works, e.g. `npx serve demo-dist`.) Open `/` and the SPA
redirects to `/dashboard`. You should see: the demo banner, **System Status:
Healthy**, **WebSocket: Connected**, and CPU/Memory ticking from the faked
telemetry — with **no** network requests to any backend.

## Deploy to a static host

`demo-dist/` is a plain static bundle — upload its contents anywhere:

- **GitHub Pages:** push `demo-dist/` contents to a `gh-pages` branch (or use an
  action). If serving from a subpath (e.g. `https://user.github.io/repo/`), set
  Vite's `base` accordingly, e.g.
  `npm run build:demo -- --base=/repo/`.
- **Netlify / Vercel / S3 / Cloudflare Pages:** point the host at `demo-dist/`.
  Add an SPA fallback so unknown routes serve `index.html` (the app uses
  client-side routing via `BrowserRouter`). For a subpath-free root deploy no
  extra config is needed beyond the SPA fallback.

## Re-capture fixtures

Fixtures were captured from the test-mode backend (the same one Playwright uses).
To refresh them:

```bash
cd webui/frontend
./scripts/capture-demo-fixtures.sh
```

The script starts the test-mode backend
(`uv run python -m chatty_commander.cli.main --web --test-mode --port 8162
--no-auth`) if one isn't already running, curls each endpoint listed in
`src/demo/fixtures.ts`, pretty-prints the JSON into `src/demo/fixtures/`,
synthesizes the empty `advisors_context_stats.json` (the endpoint returns 400
"advisors not enabled" in test mode, which the SPA treats as "no agents"),
redacts any masked `bridge_token`, secret-scans every body, and stops the
backend it started.

If you add a new endpoint to the UI, add it to **both** the `dump` list in the
script and the `FIXTURES` map in `src/demo/fixtures.ts`.

## Files

```
src/demo/
  fixtures.ts            # path -> bundled fixture map (import.meta.glob)
  fixtures/*.json        # captured/synthesized static responses
  installDemoMocks.ts    # fetch + WebSocket monkeypatches
  FakeWebSocket.ts       # never-connecting WS that emits scripted frames
  DemoBanner.tsx         # dismissible "Demo mode" banner
src/index.tsx            # guarded `if (import.meta.env.VITE_DEMO)` bootstrap
.env.demo                # VITE_DEMO=1 (loaded only with --mode demo)
scripts/capture-demo-fixtures.sh
```
