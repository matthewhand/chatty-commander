# Changelog

## [0.1.1] - 2025-08-20

### Fixed

- Command executor: support both legacy and action-style schemas; tolerant mode returns False for invalid/missing commands in coverage tests; URL actions use timeout when action-style; improved keypress error handling; avoid duplicate critical logs.
- WebSocket avatar route: avoid un-awaited coroutine warning by using `asyncio.run` when no loop is present.

### Tests

- Added focused coverage tests; ensured Python suite passes via `make test`.
- JS tests: allow running on Node <22 via `tsx` loader; added ESM `shared/ascii.mjs` and updated unit test import.

## [0.2.0] - 2024-12-19

### Added

- **E2E Testing**: Comprehensive end-to-end test suite with 90% coverage gate
- **Observability**: Metrics middleware with JSON and Prometheus endpoints (`/metrics/json`, `/metrics/prom`)
- **API Endpoints**:
  - `GET /api/v1/version` - Application version and git SHA
  - `GET /api/v1/health` - Health check with uptime
  - `GET /api/v1/metrics` - Legacy metrics endpoint
- **Agents API**: Full CRUD for agent blueprints with team orchestration
- **Avatar System**: WebSocket-based avatar state broadcasting with animation selection
- **CLI Improvements**: Rich help text with examples, dry-run mode, interactive shell
- **Packaging**: PyInstaller spec with CI artifacts for Linux/macOS/Windows
- **Documentation**:
  - WebUI connectivity guide
  - Standalone install instructions
  - Example workflows and E2E smoke script

### Enhanced

- **Frontend**: React components with WebSocket provider and protected routes
- **Backend**: FastAPI with modular routers, middleware, and comprehensive error handling
- **CI/CD**: Coverage enforcement, frontend testing, artifact builds on tags
- **Developer Experience**: Makefile targets, lint/format automation, comprehensive docs

### Technical

- Thread-safe metrics registry with Counter/Gauge/Histogram/Timer
- RequestMetricsMiddleware for automatic HTTP request instrumentation
- Thinking state manager with async broadcast support
- Isolated test stores for deterministic agent testing
- OpenAPI schema parity validation

## [0.1.0] - Initial Release

- Basic CLI and web mode functionality
- Configuration management
- Core command execution framework
