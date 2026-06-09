# ChattyCommander

An advanced AI-powered voice command system with a modern Web interface, capable of executing complex workflows, system interactions, and real-time communication.

![Dashboard Preview](docs/images/dashboard.png)

## Recent Updates
- **Test Cleanup**: Removed low-quality test files (`test_cli_coverage.py`, `test_browser_analyst_perf.py`, `test_llm_processor.py`) and improved test coverage
- **Dependency Updates**: Updated voice pipeline dependencies and audio configuration APIs
- **Security Enhancements**: Fixed authentication middleware and path traversal vulnerabilities
- **UI Improvements**: DaisyUI migration for modern interface with improved accessibility

## Getting Started
We have recently restructured our documentation to make onboarding easier!

Please refer to the organized **User Guide** below:

1. [Installation Guide](docs/user-guide/01_INSTALLATION.md)
2. [Configuration Guide](docs/user-guide/02_CONFIGURATION.md)
3. [Dashboard & Web UI](docs/user-guide/03_DASHBOARD_AND_WEBUI.md)
4. [Voice Modes & Commands](docs/user-guide/04_VOICE_MODES_AND_COMMANDS.md)

## Optional: dograh voice-call integration
ChattyCommander can drive [dograh](https://github.com/dograh-tech/dograh), a self-hosted voice-call workflow engine, to place and manage phone/web calls.

- **Enable the stack**: run the dograh services alongside ChattyCommander via the compose overlay:
  ```bash
  COMPOSE_FILE=docker-compose.yml:docker-compose.dograh.yml docker compose up -d
  ```
- **Configure**: copy `.env.example` to `.env` and fill in the dograh block (`DOGRAH_BASE_URL`, `DOGRAH_API_KEY`). The `scripts/seed_dograh.py` helper can bootstrap a user, API key, and workflow for you (`--output FILE` keeps the key out of your terminal).
- **CLI**: `chatty-commander dograh health`, `... dograh list`, and `... dograh call WORKFLOW_ID PHONE_NUMBER` cover the common operations.
- **Web UI**: the dashboard shows a dograh status card with reachability and version info.

The integration is entirely optional — without dograh configured, the rest of ChattyCommander works as usual.

## Developer Documentation
Looking to modify the core functionality or add new LLM adapters?
Check out our extensive [Developer Docs](docs/developer/) section.

## Roadmap
See [`ROADMAP.md`](ROADMAP.md) for the tiered TODO list (P0/P1/P2/P3) covering the dograh integration and remaining production-readiness work.

## License
MIT License
