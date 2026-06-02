# Installation Guide

Welcome to ChattyCommander!

## Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend dashboard development)

## Setup
1. Clone the repository.
2. We recommend using `uv` for lightning-fast environment setup:
   ```bash
   uv sync
   ```
3. Copy the configuration template:
   ```bash
   cp config.json.example config.json
   ```
4. Start the application:
   ```bash
   uv run chatty-commander
   ```

## Logging

You can control the logging verbosity with the `--log-level` flag, which accepts
`DEBUG`, `INFO`, `WARNING`, or `ERROR`:

```bash
uv run chatty-commander --log-level DEBUG
```

When running in web mode, the `CHATCOMM_LOG_LEVEL` environment variable is also
honoured:

```bash
CHATCOMM_LOG_LEVEL=DEBUG uv run chatty-commander
```
