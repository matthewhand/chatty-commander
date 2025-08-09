#!/usr/bin/env bash
set -euo pipefail

# Curate commit history by squashing to periodic snapshots on a new orphan branch.
# Default granularity: monthly. Also supports quarterly.
# Produces branch: curated/history-<granularity>
# Safe: Does NOT rewrite main; builds a parallel curated branch.
#
# Usage:
#   scripts/curate_history.sh               # monthly
#   scripts/curate_history.sh quarterly     # quarterly
#   scripts/curate_history.sh monthly       # explicitly monthly
#
# Requirements:
#   - A clean working tree
#   - Bash + git + Python 3 available
#
# Notes:
#   - This creates an orphan branch and commits snapshots that represent the last state of each period.
#   - It replays diffs between period-end commits to keep commits small and readable.
#   - Pushes curated branch to origin (force) and returns to the original branch.

GRANULARITY="${1:-monthly}" # 'monthly' or 'quarterly'
TARGET_BRANCH="curated/history-${GRANULARITY}"
TMP_MONTH_HASHES="/tmp/tmp_rovodev_month_hashes_$$.txt"
TMP_PATCH="/tmp/tmp_rovodev_patch_$$.diff"

# Ensure git context
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Ensure working tree is clean
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree is dirty. Commit or stash changes before running." >&2
  exit 1
fi

# Build period -> last commit map in chronological order using Python
python3 - "$GRANULARITY" <<'PY' > "$TMP_MONTH_HASHES"
import subprocess, sys

mode = sys.argv[1]


def sh(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True).strip()

# Chronological commits
log = sh("git log --reverse --date=format:%Y-%m --format='%H %ad'")
if not log:
    sys.exit(0)

# Build mapping of period -> last hash
period_last = {}
order = []
for line in log.splitlines():
    parts = line.split()
    if len(parts) != 2:
        continue
    h, ym = parts
    y, m = ym.split('-')
    if mode == 'quarterly':
        q = (int(m) - 1) // 3 + 1
        period = f"{y}-Q{q}"
    else:
        period = ym
    period_last[period] = h
    if period not in order:
        order.append(period)

for p in order:
    print(p, period_last[p])
PY

if [[ ! -s "$TMP_MONTH_HASHES" ]]; then
  echo "No commits found; nothing to curate." >&2
  exit 0
fi

# Create orphan branch (fresh)
if git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  git branch -D "${TARGET_BRANCH}"
fi
git checkout --orphan "${TARGET_BRANCH}"
# Clear index and working tree
git rm -rf . >/dev/null 2>&1 || true
# Remove all tracked/untracked files (avoid deleting .git)
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

echo "Building curated history on ${TARGET_BRANCH} (granularity: ${GRANULARITY})..."
PREV_HASH=""
COUNT=0
while read -r PERIOD HASH; do
  COUNT=$((COUNT+1))
  if [[ -z "${PREV_HASH}" ]]; then
    # First snapshot: restore entire tree
    git restore --source="${HASH}" :/
    git add -A
    TOPS=$(git ls-tree --name-only ${HASH} | awk -F/ '{print $1}' | sort -u | tr '\n' ' ')
    git commit -m "Curated snapshot: ${PERIOD} (initial import)\n\nTop-level: ${TOPS}"
  else
    # Subsequent snapshots: apply diff from PREV -> HASH (binary-safe)
    git diff --binary "${PREV_HASH}" "${HASH}" > "$TMP_PATCH" || true
    if [[ -s "$TMP_PATCH" ]]; then
      git apply --index "$TMP_PATCH"
      AREAS=$(git diff --name-only --cached | cut -d/ -f1 | sort | uniq -c | sed 's/^\s*//;s/ /x /' | tr '\n' ', ')
      git commit -m "Curated snapshot: ${PERIOD}\n\nAreas: ${AREAS}"
      rm -f "$TMP_PATCH"
    else
      echo "No changes for ${PERIOD}; skipping commit"
    fi
  fi
  PREV_HASH="${HASH}"
done < "$TMP_MONTH_HASHES"

rm -f "$TMP_MONTH_HASHES" "$TMP_PATCH" 2>/dev/null || true

echo "Curated history created with ${COUNT} ${GRANULARITY} snapshots on ${TARGET_BRANCH}."

echo "Pushing ${TARGET_BRANCH} to origin (force)..."
git push -f -u origin "${TARGET_BRANCH}"

echo "Switching back to ${CURRENT_BRANCH}..."
git checkout "${CURRENT_BRANCH}"
