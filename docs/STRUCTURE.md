# Project Structure

This document provides a quick reference for the Chatty Commander project organization.

## Top-Level Directory Overview

```
chatty-commander/
├── config/                 # Configuration files and templates
│   ├── config.json
│   ├── config.json.template
│   └── .env.template
├── deploy/                 # Deployment and packaging
│   ├── docker/            # Container definitions
│   ├── k8s/               # Kubernetes manifests
│   ├── packaging/         # Distribution packages
│   └── Dockerfile         # Main container definition
├── frontend/               # User interface applications
│   ├── desktop-app/       # Native desktop application
│   └── web-app/           # Web-based interface
├── models/                 # AI models and assets
│   ├── chatty/            # Conversational AI models
│   ├── computer/          # Computer automation models
│   ├── idle/              # Background processing models
│   └── wakewords/         # Wake word detection models
├── server/                 # Backend services
│   ├── workers/           # Background processing workers
│   └── [server files]     # Core server implementation
├── src/chatty_commander/   # Main Python package
│   └── [core modules]     # Application logic and APIs
├── docs/                   # Documentation
├── tests/                  # Test suites
├── scripts/                # Utility scripts
└── [project files]        # README, LICENSE, etc.
```

## Quick Navigation

### Development

- **Core Logic**: `src/chatty_commander/`
- **Configuration**: `config/`
- **Tests**: `tests/`
- **Documentation**: `docs/`, `README.md`, `DEVELOPER.md`, `ARCHITECTURE.md`

### Frontend Development

- **Desktop App**: `frontend/desktop-app/`
- **Web Interface**: `frontend/web-app/`

### Backend Development

- **Server**: `server/`
- **Workers**: `server/workers/`

### AI/ML Development

- **All Models**: `models/`
- **Conversational**: `models/chatty/`
- **Computer Vision**: `models/computer/`
- **Wake Words**: `models/wakewords/`

### Deployment

- **All Deployment**: `deploy/`
- **Containers**: `deploy/docker/`
- **Kubernetes**: `deploy/k8s/`
- **Packaging**: `deploy/packaging/`

## Key Changes from Previous Structure

This organization consolidates what were previously scattered directories:

- `models-*` → `models/*/`
- `wakewords/` → `models/wakewords/`
- `app/` → `frontend/desktop-app/`
- `webui/` → `frontend/web-app/`
- `workers/` → `server/workers/`
- `docker/`, `k8s/`, `packaging/` → `deploy/*/`
- Configuration files → `config/`

This reduces top-level complexity while maintaining logical groupings and clear separation of concerns.
