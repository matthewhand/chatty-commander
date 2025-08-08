
# ChattyCommander Documentation

Generated on 2025-08-04 12:27:15

## Available Documentation

- [API Documentation](API.md) - Comprehensive API reference
- [OpenAPI Specification](openapi.json) - Machine-readable API spec
- [OpenAI-Agents Advisor Design](OPENAI_AGENTS_ADVISOR.md) - Advisor system overview and scope
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) - How CLI, GUI, and WebUI share functionality via the orchestrator

## Quick Start

1. Start the server: `python main.py --web --no-auth`
2. Open the API docs: [http://localhost:8100/docs](http://localhost:8100/docs)
3. Test the API: `curl http://localhost:8100/api/v1/status`

### OS-specific launchers

- Windows (PowerShell): `./scripts/windows/start-web.ps1 -Port 8100 -NoAuth`
- macOS (Terminal): `PORT=8100 NO_AUTH=1 ./scripts/macos/start-web.sh`

## Interactive Documentation

When the server is running, you can access interactive API documentation at:
- Swagger UI: [http://localhost:8100/docs](http://localhost:8100/docs)
- ReDoc: [http://localhost:8100/redoc](http://localhost:8100/redoc)
