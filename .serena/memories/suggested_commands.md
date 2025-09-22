# Suggested Commands for Development

## Dependency Management

- `uv sync` - Install/update all dependencies
- `uv sync --group voice` - Install voice-specific dependencies
- `uv lock --upgrade` - Update dependency versions

## Testing

- `make test` - Run full test suite (with timeout)
- `make test-cov` - Run tests with coverage report
- `make test-quick` - Run tests without timeout
- `make test-web` - Run web-specific tests
- `make test-cli` - Run CLI-specific tests
- `make test-integration` - Run integration tests
- `make test-perf` - Run performance tests
- `uv run pytest -q` - Quick test run
- `uv run pytest --cov=src --cov-report=html` - Generate HTML coverage

## Code Quality

- `make lint` - Check code style with ruff
- `make format` - Check formatting with black
- `make format-fix` - Auto-fix formatting and simple lint issues
- `make type-check` - Run type checking with mypy
- `make security-check` - Run security analysis with bandit
- `make pre-commit` - Run all pre-commit hooks
- `uv run ruff check . --fix` - Auto-fix ruff issues
- `uv run black .` - Format code with black

## Development Servers

- `make dev` - Start development server with auto-reload
- `make serve` - Start production server
- `make debug` - Start server with debug logging
- `uv run python main.py --web --no-auth --port 8100` - Web server (dev mode)
- `uv run python main.py --orchestrate --enable-text --web --no-auth` - Orchestrator with text and web

## CLI Operations

- `uv run chatty run` - Start voice recognition
- `uv run chatty gui` - Launch desktop GUI
- `uv run chatty config` - Interactive configuration
- `uv run chatty list` - List available commands
- `uv run chatty exec <command> --dry-run` - Dry-run a command

## Build & Deployment

- `make build-exe` - Build standalone CLI binary
- `make docker-build` - Build Docker image
- `make docker-run` - Run Docker container
- `make api-docs` - Generate API documentation

## Maintenance

- `make clean` - Clean build artifacts
- `make clean-all` - Clean all caches and artifacts
- `make health` - Check server health
- `make audit` - Run security audit
- `make gate` - Run development gate checks
- `make guard` - Run guard tests

## Utility Commands (Linux)

- `ls -la` - List files with details
- `find . -name "*.py"` - Find Python files
- `grep -r "pattern" src/` - Search for patterns in source
- `git status` - Check git status
- `git diff` - Show changes
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes
- `git push` - Push to remote

## Guidelines

- Always run `make test` before committing
- Use `make format-fix` to auto-fix style issues
- Run `make lint` to check for code quality issues
- Use `uv` for all Python operations (not pip)
- Prefer `make` targets for common tasks
- Test coverage should be 85%+
- All tests must pass before merging
