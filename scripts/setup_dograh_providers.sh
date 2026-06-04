#!/usr/bin/env bash
# One-shot setup for self-hosted dograh voice providers (ROADMAP P0/P1):
#   1. (optional, --rotate) rotate DOGRAH_OSS_JWT_SECRET, restart dograh, re-seed API key
#   2. start the Speaches overlay (local Whisper STT + Kokoro TTS)
#   3. download the STT/TTS models into the speaches container
#   4. point dograh's LLM at an OpenAI-compatible endpoint and STT/TTS at speaches
#
# Usage:
#   scripts/setup_dograh_providers.sh [--rotate]
#
# Reads from .env: DOGRAH_API_KEY, DOGRAH_BASE_URL, BEARER_API_KEY,
#                  OPENAI_BASE_URL, OPENAI_MODEL
# Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=.env
SPEACHES_PORT=8960
SPEACHES_INTERNAL_URL="http://speaches:8000/v1"   # dograh-api reaches it on the shared docker network
STT_MODEL="Systran/faster-distil-whisper-small.en"
TTS_MODEL="speaches-ai/Kokoro-82M-v1.0-ONNX"
TTS_VOICE="af_heart"

die() { echo "ERROR: $*" >&2; exit 1; }
envget() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2-; }

[ -f "$ENV_FILE" ] || die ".env not found (run from repo root)"
DOGRAH_BASE_URL=$(envget DOGRAH_BASE_URL); DOGRAH_BASE_URL=${DOGRAH_BASE_URL:-http://localhost:8020}

# --- 1. optional secret rotation -------------------------------------------
if [ "${1:-}" = "--rotate" ]; then
  cp "$ENV_FILE" "$ENV_FILE.bak.rotation" && chmod 600 "$ENV_FILE.bak.rotation"
  NEW_SECRET=$(openssl rand -hex 32)
  sed -i "s/^DOGRAH_OSS_JWT_SECRET=.*/DOGRAH_OSS_JWT_SECRET=${NEW_SECRET}/" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "JWT secret rotated (backup: $ENV_FILE.bak.rotation)"
  docker compose up -d --force-recreate dograh-api dograh-ui
  echo "Waiting for dograh-api to be healthy..."
  for _ in $(seq 1 30); do
    curl -fsS -m 2 "$DOGRAH_BASE_URL/api/v1/health" >/dev/null 2>&1 && break; sleep 2
  done
  # Re-seed a fresh API key (old JWTs are now invalid)
  uv run python scripts/seed_dograh.py --output /tmp/dograh-seed.env
  NEW_KEY=$(grep -E '^DOGRAH_API_KEY=' /tmp/dograh-seed.env | cut -d= -f2-)
  rm -f /tmp/dograh-seed.env
  [ -n "$NEW_KEY" ] || die "re-seed did not produce DOGRAH_API_KEY"
  sed -i "s/^DOGRAH_API_KEY=.*/DOGRAH_API_KEY=${NEW_KEY}/" "$ENV_FILE"
  echo "DOGRAH_API_KEY re-seeded."
fi

DOGRAH_API_KEY=$(envget DOGRAH_API_KEY)
[ -n "$DOGRAH_API_KEY" ] || die "DOGRAH_API_KEY not set in .env"

# --- 2. speaches up ----------------------------------------------------------
if ! grep -E '^COMPOSE_FILE=' "$ENV_FILE" | grep -q speaches; then
  echo "NOTE: docker-compose.speaches.yml is not in COMPOSE_FILE; appending for this run."
  export COMPOSE_FILE="$(envget COMPOSE_FILE):docker-compose.speaches.yml"
fi
docker compose up -d speaches
echo "Waiting for speaches..."
for _ in $(seq 1 60); do
  curl -fsS -m 2 "http://localhost:${SPEACHES_PORT}/health" >/dev/null 2>&1 && break; sleep 2
done
curl -fsS -m 2 "http://localhost:${SPEACHES_PORT}/health" >/dev/null || die "speaches did not become healthy"

# --- 3. model downloads (no-op if present) ----------------------------------
echo "Downloading STT model: $STT_MODEL"
curl -fsS -X POST "http://localhost:${SPEACHES_PORT}/v1/models/${STT_MODEL}" || true
echo "Downloading TTS model: $TTS_MODEL"
curl -fsS -X POST "http://localhost:${SPEACHES_PORT}/v1/models/${TTS_MODEL}" || true

# --- 4. dograh provider configuration ---------------------------------------
LLM_BASE_URL=$(envget OPENAI_BASE_URL); LLM_BASE_URL=${LLM_BASE_URL:-https://api.openai.com/v1}
LLM_MODEL=$(envget OPENAI_MODEL); LLM_MODEL=${LLM_MODEL:-gpt-4.1-mini}
LLM_API_KEY=$(envget BEARER_API_KEY)
[ -n "$LLM_API_KEY" ] || die "BEARER_API_KEY not set in .env (needed for the LLM provider)"

CURRENT=$(curl -fsS -H "X-API-Key: $DOGRAH_API_KEY" "$DOGRAH_BASE_URL/api/v1/user/configurations/user")
NEW=$(python3 - "$LLM_BASE_URL" "$LLM_MODEL" "$LLM_API_KEY" "$SPEACHES_INTERNAL_URL" "$STT_MODEL" "$TTS_MODEL" "$TTS_VOICE" <<'PYEOF'
import json, sys
llm_base, llm_model, llm_key, sp_url, stt_model, tts_model, tts_voice = sys.argv[1:8]
cfg = json.loads(sys.stdin.read())
cfg["llm"] = {"provider": "openai", "model": llm_model, "base_url": llm_base, "api_key": llm_key}
cfg["stt"] = {"provider": "speaches", "model": stt_model, "base_url": sp_url, "language": "en"}
cfg["tts"] = {"provider": "speaches", "model": tts_model, "voice": tts_voice, "base_url": sp_url, "speed": 1.0}
print(json.dumps(cfg))
PYEOF
<<<"$CURRENT")

curl -fsS -X PUT -H "X-API-Key: $DOGRAH_API_KEY" -H 'Content-Type: application/json' \
  -d "$NEW" "$DOGRAH_BASE_URL/api/v1/user/configurations/user" >/dev/null
echo "Provider config updated."

# --- validate ----------------------------------------------------------------
echo "Validation result:"
curl -fsS -H "X-API-Key: $DOGRAH_API_KEY" "$DOGRAH_BASE_URL/api/v1/user/configurations/user/validate" || true
echo
echo "Done. Try a webcall at http://localhost:3020 — STT/TTS now run locally via speaches."
