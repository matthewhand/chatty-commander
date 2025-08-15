#!/usr/bin/env bash
# Error-tolerant triage. No 'set -e'. We keep going and log failures.
set -o pipefail
set +e
trap 'ec=$?; echo "[warn] command failed (exit=$ec): $BASH_COMMAND" >&2; true' ERR

REPORT="reports/triage_$(date -Iseconds | tr ':' '-').md"
mkdir -p reports

exec > >(tee -a "$REPORT") 2>&1

divider(){ printf '\n%s\n' "-------------------------------------------------------------------------------"; }
section(){ divider; printf '## %s\n' "$1"; }
showfile(){ f="$1"; cap="${2:-250}"; if [ -f "$f" ]; then
  echo "### File: $f (first $cap lines)"; nl -ba "$f" | sed -n "1,${cap}p"
else echo "### File: $f (missing)"; fi; }
grep_cap(){ cap="${1:-200}"; shift || true; echo "\$ $*"
  out="$({ eval "$*" || true; } | sed -n "1,${cap}p")"
  printf "%s\n" "$out"
  cnt=$(printf "%s\n" "$out" | wc -l | tr -d ' ')
  [ "$cnt" -ge "$cap" ] && echo "[…truncated to $cap lines…]" || true
}

section "System"
printf "**PWD:** %s\n" "$(pwd)"
printf "**OS:** " ; uname -a || true
printf "**Python:** " ; (python3 --version || true)
printf "**Node:** " ; (node -v || echo "node not found")
printf "**pnpm:** " ; (pnpm -v || echo "pnpm not found")
printf "**Docker:** " ; (docker -v || echo "docker not found")
printf "**Git:** " ; (git --version || echo "git not found")

section "Git status & recent commits"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git remote -v || true
  git status -sb || true
  echo; git log --oneline --decorate -n 20 || true
  echo; echo "### Branches (top 30 by recency)"; git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/heads | head -n 30
else
  echo "Not a git repo."
fi

section "Worktrees overview"
git worktree list 2>/dev/null || echo "no worktrees"
echo; echo "### Prune preview (safe):"
git worktree prune -n -v 2>/dev/null || true

section "Top-level layout (depth 2, filtered)"
prune='\( -path "./.git" -o -path "./node_modules" -o -path "./dist" -o -path "./build" -o -path "./__pycache__" -o -path "./logs" -o -path "./.venv" -o -path "./.venv_*" -o -path "./.mypy_cache" \) -prune'
eval find . -maxdepth 2 $prune -o -type d -print | sed 's|^\./||' | sort

section "Largest files/dirs (top 25)"
du -ah . 2>/dev/null | sort -hr | head -n 25

section "Key docs (first 200-300 lines)"
showfile README.md 300
showfile PROGRESS.md 200
showfile TODO.md 200
showfile MIGRATING.md 200
showfile CHANGELOG.md 200
showfile CONTRIBUTING.md 200

section "Build & config files"
showfile Makefile 200
showfile Dockerfile 200
showfile docker-compose.yml 200
showfile pyproject.toml 300
showfile pytest.ini 200
showfile pnpm-workspace.yaml 200
showfile mkdocs.yml 200
showfile webui_openapi_spec.yaml 200

section "Configs (JSON masked)"
if [ -f config.json ]; then
  echo "### File: config.json (masked, first 300 lines)"
  ./scripts/mask_json.py config.json | sed -n '1,300p'
else
  echo "config.json missing"
fi

section "Package manifests"
if command -v node >/dev/null 2>&1 && [ -f package.json ]; then
  echo "### package.json (pretty, first 400 lines)"; node -p "JSON.stringify(require('./package.json'), null, 2)" | sed -n '1,400p'
else
  showfile package.json 300
fi

section "Code stats"
py_count=$(find src server app utils workers shared -type f -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
ts_count=$(find src webui -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' \) 2>/dev/null | wc -l | tr -d ' ')
echo "**Python files:** $py_count"
echo "**TS/JS files:** $ts_count"
echo
echo "### Top Python entry points (first 120 lines each)"
for f in command_executor.py config.py conftest.py run_tests.sh ; do showfile "$f" 120; done

section "Models & assets dirs"
for d in models-chatty models-computer models-idle wakewords data; do
  if [ -d "$d" ]; then
    echo "### Dir: $d"; find "$d" -maxdepth 2 -type f | sed -n '1,80p'
  fi
done

section "Known failing logs / tests"
latest_test=$(ls -1t test_results_*.txt 2>/dev/null | head -n1 || true)
if [ -n "${latest_test:-}" ]; then
  echo "**Latest test file:** $latest_test"
  echo "### Tail (200 lines)"; tail -n 200 "$latest_test" || true
  echo "### Summary lines"; grep -E "FAILED|ERROR|passed|skipped|warning|Traceback" -n "$latest_test" || true
else
  echo "No test_results_*.txt files found."
fi
[ -f test.log ] && { echo "### test.log (tail 200)"; tail -n 200 test.log; }

section "Greps: TODO/FIXME/HACK + obvious errors"
grep_cap 250 "grep -RInE 'TODO|FIXME|HACK|XXX' -- . | grep -vE 'node_modules|dist|build|__pycache__|.git' || true"
grep_cap 200 "grep -RInE 'TypeError|ImportError|ModuleNotFoundError|Unhandled|UnhandledPromiseRejection|DeprecationWarning' -- logs tests test_results_*.txt 2>/dev/null || true"

section "Server & WebUI entry points (first 180-200 lines)"
for f in server app src/webui/index.* webui/package.json webui/README.md ; do showfile "$f" 200; done

section "K8s and packaging"
showfile k8s/README.md 200
for f in k8s/*.yaml packaging/*; do [ -e "$f" ] && showfile "$f" 120; done

divider
echo "# End of triage. Saved to: $REPORT"
