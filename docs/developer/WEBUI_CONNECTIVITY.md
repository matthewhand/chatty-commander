# WebUI Connectivity

How the React frontend connects to the Python FastAPI backend.

## Default Ports

| Service | Port | URL |
|---------|------|-----|
| FastAPI backend | 8100 | `http://localhost:8100` |
| React dev server | 3000 | `http://localhost:3000` |
| WebSocket (avatar) | 8100 | `ws://localhost:8100/avatar/ws` |
| API docs (Swagger) | 8100 | `http://localhost:8100/docs` |

## Starting Both Services

**Backend (dev, no auth):**
```bash
uv run python main.py --web --no-auth --port 8100
```

**Frontend (React dev server):**
```bash
cd webui/frontend
npm install
npm run start
```

Or run everything at once with `pnpm`:
```bash
pnpm --filter app dev & pnpm --filter server dev
```

## CORS Configuration

In `--no-auth` mode, CORS is permissive, allowing requests from `http://localhost:3000`.

In production (auth enabled), CORS origins must be explicitly listed in the server config.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/status` | Application status |
| GET | `/api/v1/version` | Version info |
| GET | `/api/v1/config` | Get configuration |
| PUT | `/api/v1/config` | Update configuration |
| POST | `/api/v1/state` | Change application state |
| GET | `/metrics/json` | Metrics (JSON) |
| GET | `/metrics/prom` | Metrics (Prometheus) |

## WebSocket (Avatar)

The avatar GUI connects via WebSocket to receive state change notifications:

```
ws://localhost:8100/avatar/ws
```

Messages are JSON objects with `type` and `data` fields. See [AVATAR_GUI.md](AVATAR_GUI.md) for the full protocol.

## Troubleshooting

- **CORS errors** — ensure `--no-auth` is used in dev, or add your origin to allowed list
- **Connection refused** — check backend is running on the correct port
- **WebSocket disconnecting** — check for server restarts; the frontend auto-reconnects
