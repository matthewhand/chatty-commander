# Contributing to Chatty Commander

Welcome! This guide covers our development workflow, coding standards, and Git hygiene practices.

## Quick Start

1. Fork the repository and clone your fork
1. Set up your development environment: `uv sync --all-groups`
1. Create a feature branch: `git checkout -b feature/your-feature-name`
1. Make your changes following our coding standards
1. Run tests and linting: `uv run pytest && uv run ruff check`
1. Commit using conventional commits
1. Push and create a pull request

## Git Workflow and Branch Management

### Branch Naming Conventions

Use descriptive, kebab-case branch names with prefixes:

- `feature/` - New features or enhancements
  - `feature/avatar-voice-commands`
  - `feature/web-ui-dark-mode`
- `fix/` - Bug fixes
  - `fix/memory-leak-in-websocket`
  - `fix/config-validation-error`
- `docs/` - Documentation updates
  - `docs/api-reference-update`
  - `docs/installation-guide`
- `refactor/` - Code refactoring without functional changes
  - `refactor/state-manager-cleanup`
  - `refactor/extract-common-utilities`
- `test/` - Test additions or improvements
  - `test/avatar-integration-tests`
  - `test/web-server-guards`
- `chore/` - Maintenance tasks, dependency updates
  - `chore/update-dependencies`
  - `chore/cleanup-old-configs`
- `hotfix/` - Critical production fixes
  - `hotfix/security-vulnerability`
  - `hotfix/crash-on-startup`

### Protected Branches

These branches are protected and should not be deleted:

- `main` - Primary development branch
- `master` - Legacy main branch (if exists)
- `develop` - Development integration branch (if used)
- `staging` - Staging environment branch (if used)
- `production` - Production release branch (if used)

### Git Worktrees for Experimentation

For experimental work or parallel development, use Git worktrees instead of switching branches:

```bash
# Create a worktree for experimental feature
git worktree add .worktrees/experiment-name feature/experiment-name
cd .worktrees/experiment-name
# Work in isolation...

# When done, remove the worktree
cd ../..
git worktree remove .worktrees/experiment-name
```

**Important**: Never commit `.worktrees/` directories to the repository.

### Branch Cleanup

Regularly clean up old branches using our automated script:

```bash
# Preview what would be cleaned
./scripts/cleanup_branches.sh --dry-run

# Clean branches older than 30 days (default)
./scripts/cleanup_branches.sh

# Clean more aggressively (14 days, include unmerged)
./scripts/cleanup_branches.sh --days-old 14 --force
```

## Commit Guidelines

### Conventional Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/) for consistent commit messages:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code style changes (formatting, no logic changes)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks, dependency updates
- `perf` - Performance improvements
- `ci` - CI/CD changes
- `build` - Build system changes

**Examples:**

```bash
feat(avatar): add voice command recognition
fix(web): resolve memory leak in WebSocket connections
docs(api): update avatar configuration examples
test(web): add server import safety guards
chore(deps): update FastAPI to v0.104.0
```

### Commit Quality

Use our guarded commit script for better commit quality:

```bash
./scripts/guarded_commit.sh
```

This script:

- Runs pre-commit hooks
- Validates commit message format
- Ensures tests pass
- Checks for common issues

### Commit Message Guidelines

- **First line**: 50 characters or less, imperative mood
- **Body**: Wrap at 72 characters, explain what and why
- **Footer**: Reference issues, breaking changes

```
feat(avatar): add voice command recognition

Implement speech-to-text processing for avatar interactions.
Supports wake word detection and command parsing.

Closes #123
Breaking change: Requires new voice dependencies
```

## Code Quality and Testing

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:

```bash
uv run pre-commit install
```

Hooks include:

- Code formatting (ruff)
- Import sorting
- Trailing whitespace removal
- YAML validation
- Large file detection
- Merge conflict detection

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/test_web_server_guards.py  # Import safety tests
uv run pytest tests/test_git_hygiene.py        # Git hygiene tests
uv run pytest -k "not slow"                   # Skip slow tests

# Run with coverage
uv run pytest --cov=src/chatty_commander
```

### Code Linting and Formatting

```bash
# Check code style
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Format code
uv run ruff format

# Check imports
uv run ruff check --select I
```

## Optional Router Pattern

When adding optional web routers (like metrics, version, or agents endpoints), use the guarded inclusion pattern to prevent import errors:

### Required Pattern

```python
# REQUIRED pattern for OPTIONAL routers:
for _name in ("version_router", "metrics_router", "agents_router"):
    _r = globals().get(_name)
    if _r:
        app.include_router(_r)
```

### What NOT to do

```python
# BAD: Direct inclusion without guards
app.include_router(version_router)  # Fails if not imported

# BAD: Using except NameError
try:
    app.include_router(version_router)
except NameError:
    pass  # Masks real errors
```

### Why This Pattern?

1. **Import Safety**: Routers can be missing without breaking the app
1. **Test Resilience**: Tests work even when optional dependencies are unavailable
1. **Clean Fallbacks**: Minimal endpoints are provided when routers are missing
1. **Static Analysis**: No undefined variable references

### Testing

The pattern is enforced by `tests/test_web_server_guards.py`. Run these tests to verify compliance:

```bash
uv run pytest tests/test_web_server_guards.py
```

## Documentation Standards

Ensure documentation stays consistent and links remain valid:

```bash
uv sync --all-groups
uv run pydocstyle src
uv run doc8 README.md docs
uv run pytest --check-links README.md docs -q
```

These commands verify docstring style, lint the Markdown documentation, and test
that all referenced links resolve correctly.

## Development Environment

### Setup

```bash
# Clone and setup
git clone https://github.com/your-username/chatty-commander.git
cd chatty-commander
uv sync --all-groups

# Install pre-commit hooks
uv run pre-commit install

# Verify setup
uv run pytest tests/test_pkg_metadata.py
```

### Configuration

Copy `.env.template` to `.env` and configure as needed:

```bash
cp .env.template .env
# Edit .env with your settings
```

## Pull Request Process

1. **Create descriptive PR title** using conventional commit format
1. **Fill out PR template** with context and testing notes
1. **Ensure CI passes** - all checks must be green
1. **Request review** from maintainers
1. **Address feedback** promptly and professionally
1. **Squash commits** if requested before merge

### PR Checklist

- [ ] Branch follows naming conventions
- [ ] Commits follow conventional commit format
- [ ] Tests pass locally (`uv run pytest`)
- [ ] Code is formatted (`uv run ruff format`)
- [ ] No linting errors (`uv run ruff check`)
- [ ] Documentation updated if needed
- [ ] Breaking changes documented
- [ ] Related issues referenced

## Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Discord**: Join our community Discord (link in README)
- **Email**: Contact maintainers for security issues

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together.

Thank you for contributing to Chatty Commander! 🚀
