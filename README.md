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

## Optional: Dograh integration
ChattyCommander can hand a detected wake-word off to [Dograh](https://github.com/dograh-hq)'s
voice-AI workflows, turning a spoken trigger into a real phone or web call. This is
entirely **opt-in** — CC runs fully standalone without it.

To enable it, run CC and Dograh together via the Docker overlay. Set the following in
your local `.env` (the overlay also requires `DOGRAH_OSS_JWT_SECRET`):

```
COMPOSE_FILE=docker-compose.yml:docker-compose.dograh.yml
DOGRAH_OSS_JWT_SECRET=your-secure-random-secret-here
```

Then `docker compose up -d` brings up both stacks. To avoid colliding with CC's stock
ports, Dograh is remapped to **API `8020`** and **UI `3020`**; see
[`docker-compose.dograh.yml`](docker-compose.dograh.yml) for the full service/port list.

Once the stack is up, drive it from the `dograh` CLI group:

```
chatty-commander dograh health                 # check the configured dograh is reachable
chatty-commander dograh list                    # list workflows
chatty-commander dograh call WORKFLOW_ID PHONE  # place a telephony call
```

See [`ROADMAP.md`](ROADMAP.md) for integration status and remaining work.

## Developer Documentation
Looking to modify the core functionality or add new LLM adapters?
Check out our extensive [Developer Docs](docs/developer/) section.

## Roadmap
See [`ROADMAP.md`](ROADMAP.md) for the tiered TODO list (P0/P1/P2/P3) covering the dograh integration and remaining production-readiness work.

## License
MIT License
