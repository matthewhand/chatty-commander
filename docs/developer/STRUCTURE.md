# Project Structure

This document provides a quick reference for the Chatty Commander project organization.

## Top-Level Directory Overview

```
chatty-commander/
├── config.json             # Active runtime config (repo root; ConfigManager default)
├── config.json.example     # Sample config to copy to config.json
├── Dockerfile              # Container image used by the root docker-compose files
├── docker-compose.yml      # Base compose stack
├── docker-compose.dograh.yml  # Optional dograh overlay
├── config/                 # Extra config templates + example profiles
│   ├── config.json.template
│   ├── developer-tools-example.json
│   ├── full-assistant-example.json
│   └── voice-only-example.json
├── deploy/                 # Alternate deployment/packaging artifacts
│   ├── Dockerfile
│   ├── docker/            # docker-compose.yml
│   ├── monitoring/        # prometheus.yml
│   └── packaging/         # MANIFEST.in, icon.svg, run_cli.py, linux/ desktop entry
├── webui/frontend/         # React web UI (the active frontend)
├── models-idle/            # Wake-word ONNX models for the idle state
├── models-computer/        # Models for the computer state
├── models-chatty/          # Models for the chatty state
├── wakewords/              # Additional wake-word assets
├── src/chatty_commander/   # Main Python package
│   └── [core modules]     # Application logic, FastAPI server, APIs
├── docs/                   # Documentation (start with developer/ARCHITECTURE.md for Vision + current state + legacy architectures; see ROADMAP.md)
├── tests/                  # Test suites (Python) + tests/e2e (Playwright)
├── scripts/                # Utility scripts
└── [project files]        # README, LICENSE, .env.example, pyproject.toml, etc.
```

> Note: model directories are split per state at the repo root (`models-idle/`,
> `models-computer/`, `models-chatty/`) plus `wakewords/` — they are *not*
> consolidated under a single `models/` tree. Likewise `config.json` lives at the
> repo root (the `ConfigManager` default); the `config/` directory holds only
> templates and example profiles.

## Quick Navigation

### Development

- **Core Logic**: `src/chatty_commander/`
- **Configuration**: `config.json` (root) + templates/examples in `config/`
- **Tests**: `tests/`
- **Documentation**: `docs/`, `README.md`, `docs/developer/ARCHITECTURE.md`

### Frontend Development

- **Web Interface**: `webui/frontend/` (React, built with `npm run build`)

### Backend Development

- **FastAPI Server**: `src/chatty_commander/web/`

### AI/ML Development

- **Idle-state models**: `models-idle/`
- **Computer-state models**: `models-computer/`
- **Chatty-state models**: `models-chatty/`
- **Wake Words**: `wakewords/`

### Deployment

- **Primary container build**: root `Dockerfile` + `docker-compose.yml` (+ `docker-compose.dograh.yml` overlay)
- **Alternate artifacts**: `deploy/` — `deploy/docker/`, `deploy/monitoring/`, `deploy/packaging/`, and `deploy/Dockerfile`

## Notes on Layout

The active React frontend lives in `webui/frontend/`. The legacy top-level
directories from earlier experiments (`frontend/`, `server/`, `workers/`)
have been removed; they were never part of the current application.

A previously documented consolidation (single `models/` tree, all config under
`config/`, all deployment under `deploy/`) was only partly carried out. The
current tree above is authoritative: per-state `models-*/` + `wakewords/` at the
root, `config.json` at the root with templates in `config/`, and both a root
`Dockerfile`/compose stack and a separate `deploy/` set of artifacts.
