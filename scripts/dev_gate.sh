#!/usr/bin/env bash
# Non-exiting fast gate: lint + compile + smoke tests → conditional commit (+ optional push)
# Usage:
#   scripts/dev_gate.sh "chore: message"
#   scripts/dev_gate.sh --full "feat: run full test suite"
# Env:
#   SKIP_RUFF=1    → skip ruff
#   PUSH_ON_GREEN=1 → git push when green
# Notes:
#   - prefers guard tests if present
#   - prints return codes and never exits the shell

MSG=""
RUN_FULL=0
for arg in "$@"; do
  case "$arg" in
    --full) RUN_FULL=1 ;;
    *) MSG="$arg" ;;
  esac
done
[ -z "$MSG" ] && MSG="chore: fast smoke pass (lint/compile/tests green)"

echo "[prep] visual reset"
reset || true

RUFF_PATHS="src/chatty_commander/web/server.py src/chatty_commander/compat.py"
[ -f tests/test_web_server_guards.py ] && RUFF_PATHS="$RUFF_PATHS tests/test_web_server_guards.py"

echo "[1/4] lint (ruff) on hot files"
if [ -z "$SKIP_RUFF" ] && command -v ruff >/dev/null 2>&1; then
  ruff check $RUFF_PATHS --quiet
  ruff_rc=$?
else
  ruff_rc=127
fi
echo "ruff_rc=$ruff_rc"

echo "[2/4] compile & import smoke"
python - <<'PY'
import importlib, py_compile, sys
rc1=rc2=0
try:
    py_compile.compile('src/chatty_commander/web/server.py', doraise=True)
    print("server_compile=0")
except Exception as e:
    print("server_compile=1", e); rc1=1
try:
    importlib.import_module('chatty_commander')
    print("pkg_import=0")
except Exception as e:
    print("pkg_import=1", e); rc2=1
print(f"smoke_rc={(rc1 or rc2)}")
PY

echo "[3/4] pytest quick set"
if [ "$RUN_FULL" -eq 1 ]; then
  pytest -q
  py_rc=$?
else
  if [ -f tests/test_web_server_guards.py ]; then
    pytest -q tests/test_web_server_guards.py
    py_rc=$?
  else
    pytest -q tests/test_pkg_metadata.py
    py_rc=$?
  fi
fi
echo "pytest_rc=$py_rc"

# Re-evaluate RCs for gating (simple, deterministic)
pyc_rc=$(python - <<'PY'
import py_compile, sys
try: py_compile.compile('src/chatty_commander/web/server.py', doraise=True); print(0)
except Exception: print(1)
PY
)
pkg_rc=$(python - <<'PY'
import importlib
try: importlib.import_module('chatty_commander'); print(0)
except Exception: print(1)
PY
)
if [ -z "$SKIP_RUFF" ] && command -v ruff >/dev/null 2>&1; then
  ruff check $RUFF_PATHS --quiet >/dev/null 2>&1; ruff_rc_final=$?
else
  ruff_rc_final=127
fi
echo "gate_rcs: pyc=$pyc_rc pkg=$pkg_rc pytest=$py_rc ruff=$ruff_rc_final"

echo "[4/4] commit only if all green (ruff allowed to be missing)"
if [ "$pyc_rc" -eq 0 ] && [ "$pkg_rc" -eq 0 ] && [ "$py_rc" -eq 0 ] && { [ "$ruff_rc_final" -eq 0 ] || [ "$ruff_rc_final" -eq 127 ]; }; then
  git add -A >/dev/null 2>&1
  git commit -m "$MSG" >/dev/null 2>&1
  echo "commit_rc=$?"
  if [ "$PUSH_ON_GREEN" = "1" ]; then
    BR="$(git branch --show-current)"
    git push -u origin "$BR" >/dev/null 2>&1 && echo "push_rc=0" || echo "push_rc=$?"
  fi
else
  echo "[commit] skipped (keep history clean)"
fi
