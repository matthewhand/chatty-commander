# Architecture Overview

> See also [ARCHITECTURE.md](ARCHITECTURE.md) for directory-level detail.

## High-Level Design

ChattyCommander is a multi-modal AI assistant with modular components:

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│   Web UI (React)   │   Desktop GUI (Python)  │
└────────────┬────────────────────┬────────────┘
             │ HTTP/WebSocket      │ PyWebView
┌────────────▼────────────────────▼────────────┐
│              FastAPI Web Server               │
│  /api/v1/*  /metrics/*  /avatar/ws  /docs    │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│           Core Application (src/)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  Advisors│ │   Voice  │ │  Orchestrator│  │
│  │ (LLM AI) │ │(Wake Word│ │  (CLI/State) │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐                   │
│  │ LLM Mgr  │ │  Avatar  │                   │
│  │(OpenAI/  │ │ (3D GUI) │                   │
│  │ Ollama)  │ └──────────┘                   │
│  └──────────┘                                 │
└──────────────────────────────────────────────┘
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `advisors/` | LLM conversation management, personas, memory |
| `llm/` | Unified LLM backend (OpenAI, Ollama, local, mock) |
| `web/` | FastAPI server, routers, authentication |
| `cli/` | Command-line interface and REPL |
| `avatars/` | 3D avatar state management and lip-sync |
| `app/` | Configuration, state machine, orchestration |

## Communication Flows

- **REST**: `GET/POST /api/v1/*` for config, commands, agents
- **WebSocket**: `/avatar/ws` for real-time avatar animations
- **Metrics**: `/metrics/json` (JSON) and `/metrics/prom` (Prometheus)

## Security

- JWT authentication (configurable, disable with `--no-auth` for dev)
- Rate limiting: 100 req/min default
- XSS/CSRF headers via middleware

For extension points see [ADAPTERS.md](ADAPTERS.md).
