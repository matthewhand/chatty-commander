# New Contributor Guide

Welcome! This brief guide highlights a few places to explore when getting started with ChattyCommander.

1. **Run the CLI** to see the project in action:
   ```bash
   uv run python src/chatty_commander/cli.py --help
   ```
1. **Inspect `config.json`** in the repository root to learn how wake words, actions, and services are configured.
1. **Explore `src/chatty_commander/web_mode.py`** to understand how the web interface and server are implemented.
1. **Review the modules in `src/chatty_commander/advisors/`** to see how advisor behaviors and integrations are structured.
1. **Read the docs** for architecture, configuration, and adapters:
   - [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
   - [Configuration Schema](CONFIG_SCHEMA.md)
   - [Adapter and Plugin System](ADAPTERS.md)

Happy hacking!
