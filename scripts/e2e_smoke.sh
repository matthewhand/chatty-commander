#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8100}
JQ=${JQ:-jq}

info() { echo "[e2e] $*"; }

info "Health/status/version"
curl -fsS "$BASE_URL/api/v1/health" | ${JQ} . >/dev/null || true
curl -fsS "$BASE_URL/api/v1/status" | ${JQ} . >/dev/null || true
curl -fsS "$BASE_URL/api/v1/version" | ${JQ} . >/dev/null || true

info "Config PUT + GET"
curl -fsS -X PUT "$BASE_URL/api/v1/config" -H 'Content-Type: application/json' -d '{"foo":{"bar":1}}' >/dev/null || true
curl -fsS "$BASE_URL/api/v1/config" | ${JQ} . >/dev/null || true

info "State change"
curl -fsS -X POST "$BASE_URL/api/v1/state" -H 'Content-Type: application/json' -d '{"state":"computer"}' | ${JQ} . >/dev/null || true

info "Metrics"
curl -fsS "$BASE_URL/metrics/json" | ${JQ} '.counters["http_requests_total"]' >/dev/null || true

info "Agents: create -> list -> update -> delete"
BP_ID=$(curl -fsS -X POST "$BASE_URL/api/v1/agents/blueprints" -H 'Content-Type: application/json' -d '{"description":"Summarizer agent"}' | ${JQ} -r .id || echo "")
if [[ -n "$BP_ID" ]]; then
  curl -fsS "$BASE_URL/api/v1/agents/blueprints" | ${JQ} '.[] | select(.id=="'"$BP_ID"'")' >/dev/null || true
  curl -fsS -X PUT "$BASE_URL/api/v1/agents/blueprints/$BP_ID" -H 'Content-Type: application/json' -d '{"name":"SummarizerX","description":"d","persona_prompt":"p","capabilities":[],"team_role":null,"handoff_triggers":[]}' >/dev/null || true
  curl -fsS -X DELETE "$BASE_URL/api/v1/agents/blueprints/$BP_ID" >/dev/null || true
fi

info "Done"
