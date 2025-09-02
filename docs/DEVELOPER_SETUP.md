# ChattyCommander Developer Setup Guide

For a quick project orientation, see the [New Contributor Guide](NEW_CONTRIBUTOR_GUIDE.md).

## Prerequisites

- Python 3.11+
- uv (pip alternative)
- Git

## Setup

1. Clone repo: `git clone https://github.com/your-repo/chatty-commander.git`
1. Install deps: `uv sync --dev`
1. Set up pre-commit: `uv run pre-commit install`

## Development

### Packaging (Standalone CLI)

- Build: `uv run pyinstaller --clean -y packaging/chatty_cli.spec`

- Output binary: `dist/chatty` (or `dist/chatty.exe` on Windows)

- Smoke test: `./dist/chatty --help` and `./dist/chatty list`

- Run tests: `uv run pytest`

- Run linter: `uv run ruff check .`

- Build docs: `uv run python generate_api_docs.py`

## Contributing

- Create branch: `git checkout -b feature/xyz`
- Commit changes
- Push and create PR

For major enhancements, open an RFC issue first and follow the [RFC process](RFC_PROCESS.md).
See CONTRIBUTING.md for more.
