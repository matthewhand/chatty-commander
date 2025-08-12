# ChattyCommander Developer Setup Guide

## Prerequisites
- Python 3.11+
- uv (pip alternative)
- Git

## Setup
1. Clone repo: `git clone https://github.com/your-repo/chatty-commander.git`
2. Install deps: `uv sync --dev`
3. Set up pre-commit: `uv run pre-commit install`

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

See CONTRIBUTING.md for more.