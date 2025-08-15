#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
MSG="${1:-chore: guarded commit}"

paths=(src tests scripts)

if command -v uv >/dev/null 2>&1; then
  uv run ruff check "${paths[@]}" --fix
  uv run black "${paths[@]}"
else
  ruff check "${paths[@]}" --fix || true   # allow missing ruff
  black "${paths[@]}" || true               # allow missing black
fi

# minimal smoke tests only
if command -v pytest >/dev/null 2>&1; then
  pytest -q tests/test_pkg_metadata.py
else
  python -m pytest -q tests/test_pkg_metadata.py || python3 -m pytest -q tests/test_pkg_metadata.py
fi

git add -A && git commit -m "$MSG"
echo "✅ Guarded commit created: $MSG"
