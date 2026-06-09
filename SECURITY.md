# Security Policy

## Supported versions

Only the latest code on `main` is supported. There are no maintained release
branches yet; security fixes land on `main` and ship with the next release.

## Reporting a vulnerability

Please use [GitHub private vulnerability reporting](https://github.com/matthewhand/chatty-commander/security/advisories/new)
to report security issues. Do not open a public issue for anything you believe
is exploitable. You should receive an acknowledgement within a week.

## Authentication model (summary)

- The web API authenticates with an `X-API-Key` header enforced by
  `AuthMiddleware`, which both app factories attach by default.
- `no_auth=True` (CLI `--no-auth`) disables authentication and is intended for
  local development and tests only. Never expose a `--no-auth` server beyond
  loopback.
- The optional dograh integration authenticates outbound with `DOGRAH_API_KEY`
  from the environment; secrets belong in `.env` (gitignored) — see
  `.env.example`.

## Scope notes for researchers

Voice/wakeword processing runs locally; the attack surface of interest is the
FastAPI server (`src/chatty_commander/web/`), its WebSocket channel (`/ws`),
and the command execution layer (`src/chatty_commander/app/command_executor.py`),
which can trigger keypresses, URLs, and system actions from configured commands.
