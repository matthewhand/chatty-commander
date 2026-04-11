#!/bin/bash
PYTHONPATH=../../src uv run python -m chatty_commander.main --web --port 8100 --no-auth > server.log 2>&1 &
SERVER_PID=$!
sleep 5
pnpm test:e2e tests/e2e/telemetry.spec.ts tests/e2e/websocket_experience.spec.ts tests/e2e/screenshots.spec.ts
kill $SERVER_PID
