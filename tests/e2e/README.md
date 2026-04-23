# E2E Tests with Playwright

This directory contains end-to-end tests using Playwright for browser automation.

## Prerequisites

```bash
pip install pytest-playwright playwright
playwright install chromium
```

## Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_web_e2e.py -v

# Run with headed browser (visible)
pytest tests/e2e/ --headed -v

# Run with specific browser
pytest tests/e2e/ --browser chromium -v
```

## Test Structure

- `conftest.py` - Playwright fixtures and live server setup
- `test_web_e2e.py` - Core web API endpoint tests
- `test_avatar_e2e.py` - Avatar-specific E2E tests

## Notes

- E2E tests start a live FastAPI server on a random available port
- Tests are automatically skipped if Playwright is not installed
- The server runs in `--no-auth` mode for testing
- Tests use browser's fetch API to test endpoints from a real browser context
