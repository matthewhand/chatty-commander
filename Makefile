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

# Lint (placeholder; recommend ruff/black configs in pyproject.toml)
lint:
	@echo "Add ruff/black configs in pyproject.toml to enable linting targets."

# Format (placeholder)
format:
	@echo "Add formatter configs in pyproject.toml to enable formatting targets."

# Clean caches
clean:
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run all steps
all: install test clean
