#!/usr/bin/env bash
set -o pipefail; set +e
echo "### git worktree list"
git worktree list 2>/dev/null || exit 0
echo
echo "### Stale worktrees (dir missing or branch gone)"
while read -r path sha rest; do
  [ -z "$path" ] && continue
  if [ ! -d "$path/.git" ]; then echo "MISSING_DIR: $path ($sha)"; fi
done < <(git worktree list --porcelain | awk '/worktree /{print $2} /HEAD /{print $2}')
echo
echo "### Branch recency (top 30)"
git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/heads | head -n 30
