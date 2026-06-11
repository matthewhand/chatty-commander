#!/usr/bin/env bash
#
# capture-demo-fixtures.sh — re-capture the static demo fixtures from a
# locally-running test-mode backend.
#
# The fully-static demo (VITE_DEMO build) serves pre-recorded JSON instead of
# hitting a backend. This script regenerates those fixtures by curling the
# test-mode FastAPI server and writing pretty-printed JSON into
# src/demo/fixtures/. It secret-scans every body and redacts masked tokens.
#
# Usage:
#   ./scripts/capture-demo-fixtures.sh           # starts/stops its own backend
#   PORT=8162 ./scripts/capture-demo-fixtures.sh # custom port
#
# Requires: curl, python3, and (to auto-start the backend) `uv` at repo root.
set -euo pipefail

PORT="${PORT:-8162}"
BASE="http://localhost:${PORT}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXDIR="${HERE}/../src/demo/fixtures"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
mkdir -p "${FIXDIR}"

BE_PID=""
cleanup() {
  if [[ -n "${BE_PID}" ]]; then
    echo "Stopping backend (pid ${BE_PID})..."
    kill "${BE_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Start the backend only if nothing is already answering on the port.
if ! curl -s -m 2 "${BASE}/health" >/dev/null 2>&1; then
  echo "Starting test-mode backend on :${PORT} ..."
  (
    cd "${REPO_ROOT}"
    PYTHONPATH=src nohup uv run python -m chatty_commander.cli.main \
      --web --test-mode --port "${PORT}" --no-auth >/tmp/demo-be.log 2>&1 &
    echo $! >/tmp/demo-be.pid
  )
  BE_PID="$(cat /tmp/demo-be.pid)"
  for _ in $(seq 1 30); do
    curl -s -m 2 "${BASE}/health" >/dev/null 2>&1 && break
    sleep 1
  done
fi

# path -> output filename. Keep in sync with src/demo/fixtures.ts.
dump() {
  local path="$1" file="$2"
  local code
  code="$(curl -s -m 5 -o /tmp/_demo_body -w '%{http_code}' "${BASE}${path}")"
  if [[ "${code}" == "200" ]]; then
    python3 -m json.tool /tmp/_demo_body >"${FIXDIR}/${file}" 2>/dev/null \
      || cp /tmp/_demo_body "${FIXDIR}/${file}"
    echo "  [200] ${path} -> ${file}"
  else
    echo "  [${code}] ${path} -> SKIPPED (using existing/synthesized fixture)"
  fi
}

echo "Capturing fixtures from ${BASE} ..."
dump "/health"                    health.json
dump "/api/v1/status"             status.json
dump "/api/v1/config"             config.json
dump "/api/v1/state"              state.json
dump "/api/v1/metrics"            metrics.json
dump "/api/v1/commands"           commands.json
dump "/api/audio/devices"         audio_devices.json
dump "/api/v1/audio/devices"      v1_audio_devices.json
dump "/api/themes"                themes.json
dump "/api/v1/dograh/status"      dograh_status.json
dump "/api/v1/dograh/call-state"  dograh_call_state.json
dump "/api/v1/dograh/workflows"   dograh_workflows.json
dump "/api/v1/advisors/personas"  advisors_personas.json

# advisors/context/stats returns 400 (advisors disabled) in test mode; the SPA
# treats that as "no agents". Synthesize a valid empty-but-structured body so
# the dashboard renders a clean state instead of an error.
echo '{
    "contexts": {},
    "total": 0
}' >"${FIXDIR}/advisors_context_stats.json"
echo "  [synth] /api/v1/advisors/context/stats -> advisors_context_stats.json"

# Redact any masked bridge token defensively (test mode masks it already).
python3 - "${FIXDIR}/config.json" <<'PY'
import json, sys
p = sys.argv[1]
with open(p) as f:
    cfg = json.load(f)
ws = cfg.get("web_server", {})
if ws.get("bridge_token"):
    ws["bridge_token"] = "<REDACTED>"
with open(p, "w") as f:
    json.dump(cfg, f, indent=2)
PY

echo "Secret-scanning fixtures ..."
if grep -rliE 'sk-[a-zA-Z0-9]{16,}|bearer [a-z0-9._-]{16,}|eyJ[a-zA-Z0-9_-]{16,}\.' "${FIXDIR}"/*.json; then
  echo "!! Potential secret(s) found above — review and redact to <REDACTED> before committing." >&2
  exit 1
fi
echo "No high-confidence secrets found."
echo "Done. Fixtures written to ${FIXDIR}"
