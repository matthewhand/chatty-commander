#!/usr/bin/env python3
"""
Produce a dry-run proposal for curating/squashing history into readable batches.

- Scans git commits and groups pre-boundary commits by period (monthly or quarterly).
- Optionally applies smart thematic merging of adjacent periods (e.g., merge tiny months with
  similar top-level areas).
- Outputs a Markdown proposal including suggested curated commit messages per batch and what
  will remain intact after the boundary date.

Usage:
  python scripts/curate_history_proposal.py \
      --boundary 2025-08-05 \
      --granularity monthly \
      --smart true \
      --max-commits-per-batch 30 \
      --min-overlap 0.4

Note: Run this from the root of a git repo.
"""
from __future__ import annotations

import argparse
import dataclasses as dc
import datetime as dt
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable


@dc.dataclass
class Commit:
    sha: str
    date: dt.date
    subject: str
    top_paths: Counter


def sh(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def parse_git_log() -> list[Commit]:
    # We print commit header lines then changed file paths; commits separated by blank lines
    cmd = (
        "git log --reverse --date=short "
        "--pretty=format:%H\t%ad\t%s --name-only"
    )
    out = sh(cmd)
    commits: list[Commit] = []
    sha = date = subj = None
    files: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            # end of block
            if sha and date and subj is not None:
                tp = Counter(_top_path(p) for p in files if p)
                commits.append(
                    Commit(sha=sha, date=_parse_date(date), subject=subj, top_paths=tp)
                )
            sha = date = subj = None
            files = []
            continue
        if '\t' in line:
            # new commit header
            if sha and date and subj is not None:
                tp = Counter(_top_path(p) for p in files if p)
                commits.append(
                    Commit(sha=sha, date=_parse_date(date), subject=subj, top_paths=tp)
                )
                files = []
            parts = line.split('\t', 2)
            if len(parts) == 3:
                sha, date, subj = parts
            else:
                # Fallback if subject contains tabs weirdly
                sha = parts[0]
                date = parts[1] if len(parts) > 1 else "1970-01-01"
                subj = parts[2] if len(parts) > 2 else ""
        else:
            files.append(line.strip())
    # Final flush
    if sha and date and subj is not None:
        tp = Counter(_top_path(p) for p in files if p)
        commits.append(Commit(sha=sha, date=_parse_date(date), subject=subj, top_paths=tp))
    return commits


def _parse_date(s: str) -> dt.date:
    y, m, d = map(int, s.split("-"))
    return dt.date(y, m, d)


def _top_path(path: str) -> str:
    # Normalize top-level area names for readability
    if not path or path.startswith("\n"):
        return "(none)"
    top = path.split("/", 1)[0]
    return top


def period_key(d: dt.date, granularity: str) -> str:
    if granularity == "quarterly":
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}"
    return f"{d.year}-{d.month:02d}"


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    A, B = set(a), set(b)
    if not A and not B:
        return 1.0
    return len(A & B) / max(1, len(A | B))


@dc.dataclass
class Batch:
    period_label: str
    start: dt.date
    end: dt.date
    commits: list[Commit]
    areas: Counter

    def title(self) -> str:
        if not self.areas:
            return f"Curated: {self.period_label}"
        top = [k for k, _ in self.areas.most_common(3)]
        title_map = {
            "src": "Core/Package move",
            "webui": "Web UI",
            "docs": "Docs",
            ".github": "CI",
            "tests": "Tests",
            "cli.py": "CLI",
            "cli": "CLI",
            "utils": "Utils/Logging",
            "README.md": "Docs",
        }
        # Heuristic: map known top-level dirs, else use first area
        label = None
        for t in top:
            label = title_map.get(t)
            if label:
                break
        label = label or f"{top[0] if top else self.period_label}"
        return f"Curated: {label} ({self.period_label})"

    def date_range(self) -> str:
        return f"{self.start.isoformat()} → {self.end.isoformat()}"


def build_batches(
    commits: list[Commit],
    *,
    boundary: dt.date,
    granularity: str,
    smart: bool,
    max_commits_per_batch: int,
    min_overlap: float,
) -> tuple[list[Batch], int]:
    pre = [c for c in commits if c.date < boundary]
    post = [c for c in commits if c.date >= boundary]

    # Group by period
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for c in pre:
        grouped[period_key(c.date, granularity)].append(c)

    # Sort periods chronologically by first commit date
    periods = sorted(grouped.keys(), key=lambda p: grouped[p][0].date if grouped[p] else boundary)

    # Build initial monthly/quarterly batches
    batches: list[Batch] = []
    for p in periods:
        commits_p = grouped[p]
        if not commits_p:
            continue
        areas = Counter()
        for c in commits_p:
            areas.update(c.top_paths)
        batches.append(
            Batch(
                period_label=p,
                start=commits_p[0].date,
                end=commits_p[-1].date,
                commits=commits_p,
                areas=areas,
            )
        )

    if smart and len(batches) > 1:
        # Merge adjacent small/similar batches
        merged: list[Batch] = []
        i = 0
        while i < len(batches):
            cur = batches[i]
            j = i + 1
            while j < len(batches):
                nxt = batches[j]
                combined_count = len(cur.commits) + len(nxt.commits)
                overlap = jaccard(cur.areas.keys(), nxt.areas.keys())
                if combined_count <= max_commits_per_batch and overlap >= min_overlap:
                    # Merge nxt into cur
                    cur.commits.extend(nxt.commits)
                    cur.end = nxt.end
                    cur.period_label = f"{cur.period_label}+{nxt.period_label}"
                    cur.areas.update(nxt.areas)
                    j += 1
                else:
                    break
            merged.append(cur)
            i = j
        batches = merged

    return batches, len(post)


def render_markdown(batches: list[Batch], post_count: int, boundary: dt.date) -> str:
    lines = []
    lines.append("# Curated History Proposal (dry-run)\n")
    lines.append(f"Boundary: keep commits on/after {boundary.isoformat()} intact\n")
    lines.append(f"Pre-boundary batches: {len(batches)}\n")
    lines.append(f"Post-boundary commits preserved: {post_count}\n")
    lines.append("")
    # Summary table
    lines.append("## Summary\n")
    lines.append("| Batch | Periods | Date Range | Commits | Top Areas | Suggested Title |")
    lines.append("|------:|---------|------------|--------:|-----------|------------------|")
    for idx, b in enumerate(batches, 1):
        top_areas = ", ".join([a for a, _ in b.areas.most_common(3)]) or "-"
        lines.append(
            f"| {idx} | {b.period_label} | {b.date_range()} | {len(b.commits)} | {top_areas} | {b.title()} |"
        )
    lines.append("")

    # Details per batch
    lines.append("## Details\n")
    for idx, b in enumerate(batches, 1):
        lines.append(f"### Batch {idx}: {b.title()}\n")
        lines.append(f"- Periods: {b.period_label}")
        lines.append(f"- Date range: {b.date_range()}")
        lines.append(f"- Commits: {len(b.commits)}")
        top_areas = ", ".join([a for a, _ in b.areas.most_common(8)]) or "-"
        lines.append(f"- Areas: {top_areas}")
        # Show a few example subjects for flavor
        example_subjects = [c.subject for c in b.commits[:5]]
        if example_subjects:
            for s in example_subjects:
                s = s.replace("|", " ")
                lines.append(f"  - {s}")
        lines.append("")

    # Final step description
    lines.append("## Next steps\n")
    lines.append(
        "- Create an orphan curated branch and replace pre-boundary history with one commit per batch.\n"
        "- Merge main at HEAD to preserve post-boundary commits intact (original hashes).\n"
        "- We can automate this after you confirm the batch plan.\n"
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Dry-run proposal for curated history batches")
    ap.add_argument("--boundary", required=False, default="2025-08-05", help="Boundary date YYYY-MM-DD; keep commits on/after this date intact")
    ap.add_argument("--granularity", choices=["monthly", "quarterly"], default="monthly")
    ap.add_argument("--smart", type=lambda s: s.lower() in {"1", "true", "yes", "y"}, default=True)
    ap.add_argument("--max-commits-per-batch", type=int, default=30, help="Max combined commits when merging adjacent batches")
    ap.add_argument("--min-overlap", type=float, default=0.4, help="Min Jaccard overlap of areas to merge adjacent batches")
    args = ap.parse_args(argv)

    try:
        boundary = _parse_date(args.boundary)
    except Exception:
        print("Invalid --boundary date; expected YYYY-MM-DD", file=sys.stderr)
        return 2

    # Ensure git repo
    try:
        sh("git rev-parse --is-inside-work-tree")
    except Exception:
        print("Not inside a git repository.", file=sys.stderr)
        return 2

    commits = parse_git_log()
    batches, post_count = build_batches(
        commits,
        boundary=boundary,
        granularity=args.granularity,
        smart=args.smart,
        max_commits_per_batch=args.max_commits_per_batch,
        min_overlap=args.min_overlap,
    )
    md = render_markdown(batches, post_count, boundary)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
