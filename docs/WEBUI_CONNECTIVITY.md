# WebUI Connectivity Sanity

This guide helps you verify that the WebUI (React) connects to the Python backend in development.

## Backend (FastAPI)

1. Start the backend with no auth for local development:

```
uv run python src/chatty_commander/main.py --web --no-auth --port 8100
```

2. Verify health and OpenAPI docs:

- GET http://localhost:8100/api/v1/health -> 200
- Open http://localhost:8100/docs

## Frontend (React)

1. Install dependencies (first time only):

```
npm ci --prefix webui/frontend
```

2. Start dev server:

```
npm start --prefix webui/frontend
```

3. By default, the frontend proxies to http://localhost:8100 via `proxy` in package.json.

## Tips

- Use backend flag `--no-auth` for local development.
- CORS is configured in no-auth mode for development.
- Check the browser console network tab for failed requests.

## Optional Jest smoke (frontend)

You can create a simple test to ensure a fetch to `/api/v1/health` is performed. Since the backend isn’t running in CI, mock `fetch` to return a 200 response in the test.
