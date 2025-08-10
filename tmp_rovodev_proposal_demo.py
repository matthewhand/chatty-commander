#!/usr/bin/env python3
import datetime as dt
import importlib.util
import sys
from collections import Counter

spec = importlib.util.spec_from_file_location('cur', 'scripts/curate_history_proposal.py')
cur = importlib.util.module_from_spec(spec)
sys.modules['cur'] = cur  # ensure dataclasses see a registered module
spec.loader.exec_module(cur)  # type: ignore

# Synthesize a small commit history for demo purposes
boundary = cur._parse_date("2025-08-05")

commits = [
    # 2024-04 (bootstrap/ci/docs)
    cur.Commit(sha="a1", date=dt.date(2024,4,2), subject="chore: initial project structure", top_paths=Counter({"src":5, "README.md":1})),
    cur.Commit(sha="a2", date=dt.date(2024,4,10), subject="ci: add basic CI workflow", top_paths=Counter({".github":3})),
    cur.Commit(sha="a3", date=dt.date(2024,4,20), subject="docs: add API overview", top_paths=Counter({"docs":4})),
    # 2025-07 (web/advisors/cli)
    cur.Commit(sha="b1", date=dt.date(2025,7,3), subject="feat(web): FastAPI server scaffolding", top_paths=Counter({"src":6, "tests":2})),
    cur.Commit(sha="b2", date=dt.date(2025,7,12), subject="feat(advisors): add service + memory stubs", top_paths=Counter({"src":5, "tests":3})),
    cur.Commit(sha="b3", date=dt.date(2025,7,25), subject="feat(cli): UX improvements", top_paths=Counter({"cli.py":2, "tests":2})),
    # 2025-08 (post-boundary; preserved intact)
    cur.Commit(sha="c1", date=dt.date(2025,8,6), subject="chore: package CLI + console entry fix", top_paths=Counter({"src":4, "cli.py":1})),
    cur.Commit(sha="c2", date=dt.date(2025,8,9), subject="ci: uv + ruff + black + coverage", top_paths=Counter({".github":4})),
]

# Build proposal batches for pre-boundary commits
auto_batches, post_count = cur.build_batches(
    commits,
    boundary=boundary,
    granularity="monthly",
    smart=True,
    max_commits_per_batch=30,
    min_overlap=0.4,
)

md = cur.render_markdown(auto_batches, post_count, boundary)
print(md)
