# ChattyCommander Developer Setup Guide

For a quick project orientation, see the [New Contributor Guide](NEW_CONTRIBUTOR_GUIDE.md).

## Prerequisites
- Python 3.11+
- uv (pip alternative)
- Git

## Setup
1. Clone repo: `git clone https://github.com/your-repo/chatty-commander.git`
2. Install deps: `uv sync --dev`
3. Set up pre-commit: `uv run pre-commit install`

## Development
- Run tests: `uv run pytest`
- Run linter: `uv run ruff check .`
- Build docs: `uv run python generate_api_docs.py`

## Contributing
- Create branch: `git checkout -b feature/xyz`
- Commit changes
- Push and create PR

See CONTRIBUTING.md for more.
