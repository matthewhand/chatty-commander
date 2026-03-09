# Contributing to Chatty Commander

## Quick Start

1. Fork the repo and clone it locally
2. Set up your dev environment: `uv sync --all-groups`
3. Copy the example config: `cp config/.env.example .env`
4. Create a feature branch: `git checkout -b feature/your-feature-name`
5. Make changes, run tests: `uv run pytest`
6. Push and open a PR against `main`

## Branch Naming

Use kebab-case with these prefixes:

| Prefix | Use for |
|--------|---------|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation |
| `refactor/` | Refactoring |
| `test/` | Test additions |
| `chore/` | Housekeeping |
| `hotfix/` | Critical production fixes |

## Commit Style

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[scope]: <description>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`

**Examples:**
```
feat(voice): add configurable wake word threshold
fix(web): close websocket on backend shutdown
docs(api): document health endpoint response fields
chore(deps): bump fastapi to 0.116
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific files
uv run pytest tests/test_web_server_guards.py

# With coverage
uv run pytest --cov=src/chatty_commander

# Skip slow tests
uv run pytest -k "not slow"
```

## Linting and Formatting

```bash
# Check
uv run ruff check

# Auto-fix
uv run ruff check --fix

# Format
uv run ruff format
```

## Available Scripts

Useful scripts in `scripts/`:

| Script | Purpose |
|--------|---------|
| `e2e_smoke.sh` | End-to-end smoke tests against a running server |
| `run_tests.sh` | Run the full test suite |
| `cleanup_branches.sh` | Remove stale local/remote branches |
| `guarded_commit.sh` | Commit with test + lint gate |
| `deploy.sh` | Deploy the application |
| `dev_gate.sh` | Pre-push dev sanity checks |

## Optional Router Pattern

When adding new optional web routers, always use guarded inclusion to prevent startup failures:

```python
# CORRECT: guarded inclusion
for _name in ("version_router", "metrics_router", "agents_router"):
    _r = globals().get(_name)
    if _r:
        app.include_router(_r)
```

```python
# WRONG: direct inclusion will crash if the router isn't imported
app.include_router(version_router)
```

This pattern is enforced by `tests/test_web_server_guards.py`.

## Pull Request Process

1. Ensure `uv run pytest` is green
2. Ensure `uv run ruff check` passes
3. Write a clear PR title in conventional commit format
4. Reference any related issues in the description
5. Squash commits if asked by a maintainer

### PR Checklist

- [ ] Tests pass locally
- [ ] No linting errors
- [ ] Documentation updated if behavior changed
- [ ] Breaking changes noted in the PR description
- [ ] Issues referenced

## Getting Help

Open a [GitHub Issue](https://github.com/matthewhand/chatty-commander/issues) for bugs or feature requests.

## Code of Conduct

Be respectful and constructive. That's it.
