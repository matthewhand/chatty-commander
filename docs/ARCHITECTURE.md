# Chatty Commander Architecture

This document outlines the architectural design and organizational principles of Chatty Commander, a voice-controlled AI assistant system.

## System Overview

Chatty Commander is a multi-modal AI assistant that processes voice commands, executes computer tasks, and provides conversational interactions. The system is built with a modular architecture that separates concerns across different domains.

## Directory Organization

The project follows a domain-driven organization pattern, grouping related functionality into logical directories:

### Core Application (`src/chatty_commander/`)

The main Python package containing the core business logic:

- Voice processing and wake word detection
- AI model integration and conversation management
- Computer automation and task execution
- Configuration management and system coordination

### Models (`models/`)

Consolidated directory for all AI models and related assets:

- `chatty/` - Conversational AI models and prompts
- `computer/` - Computer vision and automation models
- `idle/` - Background processing and idle state models
- `wakewords/` - Wake word detection models and configurations

### Frontend Applications (`frontend/`)

User interface components separated by platform:

- `desktop-app/` - Native desktop application (formerly `app/`)
- `web-app/` - Web-based user interface (formerly `webui/`)

### Server Infrastructure (`server/`)

Backend services and worker processes:

- Core server implementation
- `workers/` - Background processing and canvas building workers
- API endpoints and service coordination

### Configuration (`config/`)

Centralized configuration management:

- Application configuration files
- Environment templates
- Runtime configuration schemas

### Deployment (`deploy/`)

Deployment and packaging artifacts:

- `docker/` - Container definitions and orchestration
- `k8s/` - Kubernetes manifests and configurations
- `packaging/` - Distribution packages and installers
- `Dockerfile` - Main container definition

## Architectural Principles

### 1. Separation of Concerns

Each directory has a clear, single responsibility:

- Models are isolated from application logic
- Frontend and backend are cleanly separated
- Configuration is centralized and environment-agnostic
- Deployment concerns are isolated from development

### 2. Platform Agnostic Design

The core system (`src/`) is designed to work across different platforms, with platform-specific implementations in dedicated directories.

### 3. Modular Model Management

AI models are organized by function rather than technology, making it easier to:

- Swap models for different use cases
- Manage model versions and updates
- Optimize resource usage per domain

### 4. Scalable Deployment

Deployment configurations support multiple environments:

- Local development
- Containerized deployment
- Kubernetes orchestration
- Package distribution

## Data Flow

1. **Voice Input**: Audio captured through frontend applications
1. **Wake Word Detection**: Processed using models in `models/wakewords/`
1. **Speech Recognition**: Converted to text using speech models
1. **Intent Processing**: Analyzed using conversational models in `models/chatty/`
1. **Task Execution**: Computer tasks executed using `models/computer/`
1. **Response Generation**: Responses generated and delivered through frontend

## Technology Stack

- **Core**: Python with async/await patterns
- **Frontend**: Multiple platforms (desktop native, web)
- **Models**: Various AI/ML frameworks
- **Server**: TypeScript/Node.js with worker processes
- **Deployment**: Docker, Kubernetes, native packaging

## Development Workflow

The reorganized structure supports efficient development:

1. **Model Development**: Work in `models/` without affecting application logic
1. **Frontend Development**: Independent development in `frontend/` subdirectories
1. **Backend Development**: Server and worker development in `server/`
1. **Configuration Changes**: Centralized in `config/` directory
1. **Deployment**: Self-contained in `deploy/` directory

This architecture enables parallel development across different domains while maintaining clear boundaries and dependencies.
