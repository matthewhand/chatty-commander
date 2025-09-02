# Chatty-Commander Cleanup Plan (Scaffold)

## 1) Baseline

- Re-run `scripts/triage.sh` and attach REPORT.
- Decide canonical package managers: Python (uv) + Node (pnpm).

## 2) Tests

- Make `run_tests.sh` emit JUnit + coverage to `reports/`.
- Track flaky tests and top failures.

## 3) Lint/Format

- Python: ruff + black (pre-commit).
- JS/TS: biome or eslint+prettier.

## 4) Structure

- Move models-\* -> models/.
- Add `docs/quickstart.md` with copy-paste snippets.

## 5) CI

- Single entry Make targets: make fmt, make lint, make test, make build.

(Expand as we discover issues.)
