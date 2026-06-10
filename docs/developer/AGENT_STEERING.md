# Steering charter — autonomous roadmap completion

Owner-approved contract for agents working this repo autonomously. See the
conversation-portable version in the repo owner's records; this copy is the
in-repo source of truth.

## Mission
Work `ROADMAP.md` to completion in priority order: P0 leftovers → P1 →
Security backlog → P2 (voice-test e2e, hardening leftovers, then WebRTC
bridge / UI consolidation as scoped prototypes). Re-verify
`FEATURE_STATUS.md` rows before acting on them.

## Exclusions (owner actions — leave open, flag in status updates)
- Rotate dograh keys at provider; telephony provider setup
- Deleting the 13 unmerged remote branches (commands in ROADMAP.md)
- tailwind 3→4 migration (parked pending owner sign-off)

## Working agreement (PR-based)
1. Never commit to `main` directly. Branch per batch: `agent/<topic>-<n>`.
2. Fan out with disjoint per-agent file ownership; agents never run git;
   the orchestrator commits per logical group, conventional messages.
3. Definition of done per batch (all required before merge):
   - `uv run pytest -q --no-cov` green; `ruff check .` and `mypy src` clean
   - frontend `npm run test` and `npm run build` green
   - Docker proof: build the image, run the CLI smoke, and for web-affecting
     changes serve `--no-auth` in the container and curl `/health` plus one
     changed endpoint; remove test images afterwards (disk is tight)
   - PR body: what/why, test evidence, docker evidence, ROADMAP items closed
   - `gh pr merge --squash --delete-branch`, pull main, tick ROADMAP boxes
4. Status update every ~15 minutes: batch, agents running, PRs opened/merged.
5. Blocked >2 cycles → mark ⚠ in ROADMAP.md with the blocker, move on.
6. Sources of truth: ROADMAP.md, FEATURE_STATUS.md, CLAUDE.md. Never trust
   pre-`3ac5ea05` branches or PRs.

## Batch order
1. voice-test Playwright e2e (fake media stream)
2. Security backlog (6 verify-then-fix topics)
3. Frontend leftovers (real audio test handlers; legacy dir deletion)
4. Python coverage thin areas (ws.py, models.py, avatar_ws.py)
5. AuthN/AuthZ depth (design PR first)
6. WebRTC bridge scoped spike
