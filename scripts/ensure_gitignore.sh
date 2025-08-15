#!/usr/bin/env bash
set -o pipefail; set +e
add() { grep -qxF "$1" .gitignore 2>/dev/null || echo "$1" >> .gitignore; }
add "reports/"
add "logs/"
add "build/"
add "dist/"
add ".ruff_cache/"
add ".pytest_cache/"
add ".uv-cache/"
add ".uv_cache/"
add ".uvcache/"
add ".venv_prmerge/"
add "webui/frontend/node_modules/"
add "webui/node_modules/"
