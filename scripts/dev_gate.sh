#!/usr/bin/env bash
# Non-exiting fast gate: lint + compile + smoke → conditional commit
# Usage: scripts/dev_gate.sh "chore: message"
# Env:   SKIP_RUFF=1  (skip ruff)   PUSH_ON_GREEN=1 (git push when green)

MSG="${1:-chore: fast smoke pass (lint/compile/tests green)}"

echo "[prep] visual reset"; reset || true

RUFF_PATHS="src/chatty_commander/web/server.py src/chatty_commander/compat.py"
[ -f tests/test_web_server_guards.py ] && RUFF_PATHS="$RUFF_PATHS tests/test_web_server_guards.py"

echo "[1/3] ruff hot paths"
if [ -z "$SKIP_RUFF" ] && command -v ruff >/dev/null 2>&1; then
  ruff check $RUFF_PATHS --quiet; ruff_rc=$?
else
  ruff_rc=127
fi
echo "ruff_rc=$ruff_rc"

echo "[2/3] compile + smoke"
tmp_rc_dir="$(mktemp -d)"
python - <<PY
import py_compile, sys, pathlib
rc = 0
try:
    py_compile.compile("src/chatty_commander/web/server.py", doraise=True)
except py_compile.PyCompileError as e:
    rc = 1
print(rc, file=open("${tmp_rc_dir}/server_compile.rc","w"))
print(f"server_compile_rc={rc}")
PY
server_compile_rc="$(cat "${tmp_rc_dir}/server_compile.rc" 2>/dev/null || echo 1)"

pytest -q tests/test_pkg_metadata.py
smoke_rc=$?
echo "pytest_smoke_rc=$smoke_rc"

echo "gate: ruff=$ruff_rc compile=$server_compile_rc smoke=$smoke_rc"

echo "[3/3] conditional commit (ruff 0/127 AND compile==0 AND smoke==0)"
if { [ "$ruff_rc" -eq 0 ] || [ "$ruff_rc" -eq 127 ]; } && [ "$server_compile_rc" -eq 0 ] && [ "$smoke_rc" -eq 0 ]; then
  git add -A >/dev/null 2>&1
  git commit -m "$MSG" >/dev/null 2>&1 && echo "commit_rc=0" || echo "commit_rc=2"
  if [ "${PUSH_ON_GREEN:-0}" = "1" ]; then git push && echo "push_rc=0" || echo "push_rc=1"; fi
else
  echo "commit_rc=1 (skipped)"
fi
