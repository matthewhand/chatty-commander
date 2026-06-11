# Project Structure

This document provides a quick reference for the Chatty Commander project organization.

## Top-Level Directory Overview

```
chatty-commander/
├── config/                 # Configuration files and templates
│   ├── config.json
│   ├── config.json.template
│   └── *-example.json     # Sample configurations
├── deploy/                 # Deployment and packaging
│   ├── docker/            # Container definitions
│   ├── monitoring/        # Monitoring configuration
│   ├── packaging/         # Distribution packages
│   └── Dockerfile         # Main container definition
├── webui/frontend/         # React web UI (the active frontend)
├── models/                 # AI models and assets
│   ├── chatty/            # Conversational AI models
│   ├── computer/          # Computer automation models
│   ├── idle/              # Background processing models
│   └── wakewords/         # Wake word detection models
├── src/chatty_commander/   # Main Python package
│   └── [core modules]     # Application logic, FastAPI server, APIs
├── docs/                   # Documentation
├── tests/                  # Test suites
├── scripts/                # Utility scripts
└── [project files]        # README, LICENSE, .env.example, etc.
```

## Quick Navigation

### Development

- **Core Logic**: `src/chatty_commander/`
- **Configuration**: `config/`
- **Tests**: `tests/`
- **Documentation**: `docs/`, `README.md`, `docs/developer/ARCHITECTURE.md`

### Frontend Development

- **Web Interface**: `webui/frontend/` (React, built with `npm run build`)

### Backend Development

- **FastAPI Server**: `src/chatty_commander/web/`

### AI/ML Development

- **All Models**: `models/`
- **Conversational**: `models/chatty/`
- **Computer Vision**: `models/computer/`
- **Wake Words**: `models/wakewords/`

### Deployment

- **All Deployment**: `deploy/`
- **Containers**: `deploy/docker/`
- **Monitoring**: `deploy/monitoring/`
- **Packaging**: `deploy/packaging/`

## Key Changes from Previous Structure

This organization consolidates what were previously scattered directories:

- `models-*` → `models/*/`
- `wakewords/` → `models/wakewords/`
- `docker/`, `packaging/` → `deploy/*/`
- Configuration files → `config/`

The active React frontend lives in `webui/frontend/`. The legacy top-level
directories from earlier experiments (`frontend/`, `server/`, `workers/`)
have been removed; they were never part of the current application.

This reduces top-level complexity while maintaining logical groupings and clear separation of concerns.
