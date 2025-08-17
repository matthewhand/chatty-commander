#!/usr/bin/env bash
set -o pipefail
APPLY="${APPLY:-0}"
NUKE_HEAVY="${NUKE_HEAVY:-0}"
PROTECT=('data' 'wakewords' 'models-idle' 'models-computer' 'models-chatty' 'packaging/chatty_cli.spec')
confirm_rm() { # rm wrapper with protect list
  for keep in "${PROTECT[@]}"; do case "$1" in "$keep"|"$keep"/*) echo "SKIP (protected): $1"; return 0;; esac; done
  if [ "$APPLY" = "1" ]; then rm -rf -- "$1" && echo "REMOVED: $1" || echo "FAILED: $1"; else echo "DRYRUN: $1"; fi
}
# Defaults (safe)
for p in ".ruff_cache" ".pytest_cache" "logs" "build" "dist" \
         "webui/frontend/node_modules/.cache" \
         ".uv_cache" ".uvcache" ; do
  if compgen -G "$p" > /dev/null; then confirm_rm "$p"; fi
done
# Normalize uv cache: keep .uv-cache, remove legacy aliases if present
if [ -d ".uv-cache" ]; then
  : # keep canonical
fi
# Heavy (explicit)
if [ "$NUKE_HEAVY" = "1" ]; then
  for p in ".venv_prmerge" ".venv" "webui/frontend/node_modules" "webui/node_modules"; do
    [ -e "$p" ] && confirm_rm "$p"
  done
fi
echo "Done. APPLY=$APPLY, NUKE_HEAVY=$NUKE_HEAVY"
