#!/usr/bin/env bash
# Guarded commit: fail fast on conflict markers and syntax errors before committing.
set -euo pipefail
IFS=$'\n\t'
echo "[guard] scanning for conflict markers in src/ and tests/..."
if grep -R -nE '^(<<<<<<<|=======|>>>>>>>)' -- src tests >/dev/null; then
  echo "[guard] ERROR: conflict markers found; refusing to commit." >&2
  exit 2
fi
echo "[guard] py_compile smoke test..."
python - <<'PY'
import sys, pathlib, py_compile
roots = [pathlib.Path("src")]
ok = True
for root in roots:
    for p in root.rglob("*.py"):
        try: py_compile.compile(str(p), doraise=True)
        except Exception as e:
            ok = False
            print(f"[pyc] FAIL {p}: {e}", file=sys.stderr)
if not ok:
    sys.exit(3)
print("[pyc] OK")
PY
echo "[guard] staging + commit..."
git add -A
git commit -m "${1:-chore: guarded commit}"
echo "[guard] done."
