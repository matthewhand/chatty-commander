# Makefile for ChattyCommander
# Prefer uv over pip/python
.PHONY: install test test-cov test-web test-cli test-parallel test-cached clean all lint format

# Install dependencies using uv
install:
	uv sync

# Run full test suite (quiet) with a safety timeout
# GNU coreutils 'timeout' will send SIGTERM after 120s; adjust if needed.
test:
	timeout 120s uv run pytest -q --maxfail=1 || { code=$$?; echo "pytest terminated or timed out with exit code $$code"; exit $$code; }

# Coverage run with summary and timeout guard
test-cov:
	timeout 180s uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing || { code=$$?; echo "coverage run terminated or timed out with exit code $$code"; exit $$code; }

# Focused web tests
test-web:
	uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py tests/test_cors_no_auth.py

# Focused CLI tests
test-cli:
	uv run pytest -q tests/test_repl_basic.py tests/test_cli_help_and_shell.py tests/test_cli_features.py

# Run tests in parallel
test-parallel:
	uv run pytest -n auto --maxfail=1 || { code=$$?; echo "parallel pytest terminated or timed out with exit code $$code"; exit $$code; }

# Run tests with change detection caching
test-cached:
	uv run pytest --testmon || { code=$$?; echo "cached pytest terminated or timed out with exit code $$code"; exit $$code; }

# Lint using ruff (configured in pyproject.toml)
lint:
	uv run ruff check .

# Format check using black
format:
	uv run black --check .

# Auto-fix formatting and simple lint issues
format-fix:
	uv run black .
	uv run ruff check . --fix

# API docs generation
api-docs:
	uv run python -m src.chatty_commander.tools.generate_api_docs -o docs

# Development server with auto-reload
dev:
	uv run python main.py --web --no-auth --reload

# Production server
serve:
	uv run python main.py --web

# Run with debug logging
debug:
	uv run python main.py --web --no-auth --debug

# Health check
health:
	curl -f http://localhost:8000/health || echo "Server not responding"

# Database migrations (if applicable)
migrate:
	@echo "No migrations needed for this project"

# Security audit
audit:
	uv run pip-audit || echo "pip-audit not installed, run: uv add pip-audit"

# Dependency updates
update-deps:
	uv lock --upgrade

# Clean all artifacts
clean-all: clean
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.egg-info" -type d -exec rm -rf {} +

# Setup development environment
setup-dev: install
	@echo "Development environment setup complete"
	@echo "Run 'make dev' to start development server"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code quality"

# Quick test run (no timeout)
test-quick:
	uv run pytest -x --tb=short

# Integration tests
test-integration:
	uv run pytest -k "integration" -v

# Performance tests
test-perf:
	uv run pytest -k "perf" -v --durations=10

# Generate test coverage report
coverage-html:
	uv run pytest --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Type checking
type-check:
	uv run mypy src/ || echo "mypy not configured, install with: uv add mypy"

# Security linting
security-check:
	uv run bandit -r src/ || echo "bandit not installed, install with: uv add bandit"

# Pre-commit checks
pre-commit:
	pre-commit run --all-files

# Docker build
docker-build:
	docker build -t chatty-commander .

# Docker run
docker-run:
	docker run -p 8000:8000 chatty-commander

# Help
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run full test suite"
	@echo "  test-quick    - Run tests without timeout"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  test-web      - Run web-specific tests"
	@echo "  test-cli      - Run CLI-specific tests"
	@echo "  test-parallel - Run tests in parallel"
	@echo "  test-cached   - Run tests with change detection caching"
	@echo "  lint          - Check code style"
	@echo "  format        - Check code formatting"
	@echo "  format-fix    - Auto-fix formatting issues"
	@echo "  dev           - Start development server"
	@echo "  serve         - Start production server"
	@echo "  debug         - Start server with debug logging"
	@echo "  health        - Check server health"
	@echo "  clean         - Clean build artifacts"
	@echo "  clean-all     - Clean all artifacts and caches"
	@echo "  setup-dev     - Setup development environment"
	@echo "  api-docs      - Generate API documentation"
	@echo "  coverage-html - Generate HTML coverage report"
	@echo "  type-check    - Run type checking"
	@echo "  security-check- Run security analysis"
	@echo "  pre-commit    - Run pre-commit checks"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  help          - Show this help message"

# Build standalone CLI with PyInstaller
.PHONY: build-exe build-exe-all dist-clean smoke-exe

build-exe:
	uv run pyinstaller --clean -y packaging/chatty_cli.spec

.PHONY: build-exe-lite smoke-exe-lite

build-exe-lite:
	uv run pyinstaller --clean -y packaging/chatty_cli_lite.spec

smoke-exe-lite:
	@echo "Smoking built CLI (lite) in dist/ ..."
	@chmod +x dist/chatty-lite || true
	@./dist/chatty-lite --help >/dev/null || { echo "lite help failed"; exit 1; }

build-exe-all:
	@echo "Build matrix is handled in CI. Use 'make build-exe' locally."

# Development gate and guard commands
.PHONY: gate guard guard-tests

# Run development gate (ruff, compile, smoke tests)
gate:
	@if [ -x scripts/dev_gate.sh ]; then \
		scripts/dev_gate.sh "make gate"; \
	else \
		echo "Running manual gate checks..."; \
		uv run ruff check src tests && \
		python -c "import py_compile; py_compile.compile('src/chatty_commander/web/server.py', doraise=True)" && \
		uv run pytest -q tests/test_pkg_metadata.py; \
	fi

# Run guard tests (import safety, syntax safety, web server guards)
guard:
	@echo "Running guard tests..."
	uv run pytest -q tests/test_web_server_guards.py tests/test_syntax_safety.py

# Alias for guard
guard-tests: guard

# Smoke test built binary (Linux/macOS)
smoke-exe:
	@echo "Smoking built CLI in dist/ ..."
	@chmod +x dist/chatty || true
	@./dist/chatty --help >/dev/null || { echo "help failed"; exit 1; }
	@./dist/chatty list >/dev/null || { echo "list failed"; exit 1; }

# Clean caches and dist artifacts
clean:
	rm -rf .pytest_cache build dist chatty.spec
	find . -type d -name "__pycache__" -exec rm -rf {} +

dist-clean: clean
	@echo "Distribution artifacts cleaned."

# Run all steps
all: install test clean
