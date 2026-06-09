# Contributing to ChattyCommander

Thanks for your interest in contributing! This guide covers the practical details of working in this repo. A longer-form guide lives at [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md).

## Dev setup

Requires Python 3.11+ and (for frontend work) Node.js 18+. We use [uv](https://docs.astral.sh/uv/) for Python environments.

```bash
git clone https://github.com/matthewhand/chatty-commander.git
cd chatty-commander
uv sync --all-groups          # install runtime + dev dependencies
cp config.json.example config.json
cp .env.example .env          # optional: fill in only what you need
uv run chatty-commander --help
```

Frontend (React + Vite, in `webui/frontend/`):

```bash
cd webui/frontend
npm install
npm run build        # production build — must pass before you open a PR
npm run dev          # local dev server
npm run lint         # eslint
```

## Running tests

Python tests live in `tests/` (configured via `[tool.pytest.ini_options]` in `pyproject.toml`):

```bash
uv run pytest -q --no-cov                 # full suite
uv run pytest tests/test_cli.py -q --no-cov   # a single file while iterating
```

Frontend e2e tests use Playwright: `npm run test:e2e` from `webui/frontend/`.

## Code style

- Python is linted and formatted with **ruff** (line length 88, config in `pyproject.toml`):
  ```bash
  uv run ruff check src tests
  uv run ruff format src tests
  ```
- TypeScript/React is checked with `npm run lint` and `npm run type-check`.
- Keep new code under `src/chatty_commander/` (src layout); add tests alongside in `tests/`.

## Pull requests

- Branch from `main` using kebab-case prefixes: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages, e.g.
  `fix(cli): route dograh through main parser` or `feat(web): add preferences endpoints`.
- Before opening a PR: the Python suite must be green and `npm run build` must succeed.
- Keep PRs focused; reference related issues in the description.

## Reporting issues

Use [GitHub issues](https://github.com/matthewhand/chatty-commander/issues). For security vulnerabilities, see [SECURITY.md](SECURITY.md) instead of opening a public issue.
