# Makefile for ChattyCommander
# Prefer uv over pip/python
.PHONY: install test test-cov test-web test-cli clean all lint format

# Install dependencies using uv
install:
	uv sync

# Run full test suite (quiet) with a safety timeout
# GNU coreutils 'timeout' will send SIGTERM after 120s; adjust if needed.
test:
	timeout 120s uv run pytest -q || { code=$$?; echo "pytest terminated or timed out with exit code $$code"; exit $$code; }

# Coverage run with summary and timeout guard
test-cov:
	timeout 180s uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing || { code=$$?; echo "coverage run terminated or timed out with exit code $$code"; exit $$code; }

# Focused web tests
test-web:
	uv run pytest -q tests/test_web_mode_unit.py tests/test_web_mode.py tests/test_web_integration.py tests/test_cors_no_auth.py

# Focused CLI tests
test-cli:
	uv run pytest -q tests/test_repl_basic.py tests/test_cli_help_and_shell.py tests/test_cli_features.py

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
