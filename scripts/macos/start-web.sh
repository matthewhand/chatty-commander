#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8100}"
NO_AUTH="${NO_AUTH:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "Starting ChattyCommander web server on port ${PORT}..."

ARGS=(main.py --web)
if [[ "$NO_AUTH" == "1" ]]; then
  ARGS+=(--no-auth)
fi
ARGS+=(--port "$PORT")

if command -v uv >/dev/null 2>&1; then
  uv run python "${ARGS[@]}"
elif command -v python3 >/dev/null 2>&1; then
  python3 "${ARGS[@]}"
else
  python "${ARGS[@]}"
fi

echo "Server should be reachable at http://localhost:${PORT}/docs"


