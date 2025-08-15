#!/usr/bin/env bash
set -o pipefail; set +e
echo "### CLEANUP PREVIEW (no deletions). Set NUKE_HEAVY=1 in clean_apply.sh to remove heavy targets."
candidates_default=(
  ".ruff_cache" ".pytest_cache" "logs" "build" "dist"
  "webui/frontend/node_modules/.cache"
  ".uv_cache" ".uvcache" ".uv-cache"
  "src/chatty_commander.egg-info" "chatty_commander.egg-info"
  "reports/*.tmp"
)
candidates_heavy=(
  ".venv_prmerge" ".venv"
  "webui/frontend/node_modules" "webui/node_modules"
)

for p in "${candidates_default[@]}"; do
  if compgen -G "$p" > /dev/null; then du -sh "$p" 2>/dev/null || true; fi
done
echo
echo "### Heavy candidates (HEAVY=1 will delete in apply):"
for p in "${candidates_heavy[@]}"; do
  if [ -e "$p" ]; then du -sh "$p" 2>/dev/null || true; fi
done
echo
echo "### git clean (ignored only) preview:"
git clean -Xdn 2>/dev/null || true
