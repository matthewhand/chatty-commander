# New Contributor Guide

Welcome to ChattyCommander! This guide helps you get started quickly.

## First Steps

1. **Read the README** — understand what ChattyCommander does
2. **Set up your environment**: `uv sync --all-groups`
3. **Run the tests**: `uv run pytest -q`
4. **Pick an issue** — look for `good first issue` labels on GitHub

## Project Structure

```
src/chatty_commander/   # Core Python package
tests/                  # Test suite
docs/                   # Documentation
frontend/               # Web UI (React + TypeScript)
server/                 # Node.js backend workers
```

## Development Workflow

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes, write tests
4. Run `uv run pytest` and `uv run ruff check`
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details on commit conventions, PR process, and code quality standards.

## Getting Help

- Open a GitHub Issue for bugs or questions
- Check existing docs in the `docs/` folder
- See [Architecture Overview](ARCHITECTURE_OVERVIEW.md) for system design
