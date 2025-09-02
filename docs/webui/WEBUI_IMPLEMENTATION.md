# ChattyCommander WebUI Implementation Guide

## Overview

This document provides a detailed implementation roadmap for the ChattyCommander WebUI mode, which will provide a web-based interface that mirrors all desktop GUI functionality through RESTful APIs and WebSocket connections.

## Architecture Overview

### Backend (FastAPI)

- **FastAPI** for REST API endpoints
- **WebSocket** support for real-time updates
- **JWT Authentication** for security
- **SQLite/PostgreSQL** for user management
- **Pydantic** for data validation
- **AsyncIO** for concurrent operations

### Frontend (React)

- **React 18** with TypeScript
- **Material-UI (MUI)** for components
- **React Query** for API state management
- **WebSocket** client for real-time updates
- **React Router** for navigation
- **Recharts** for audio level visualization

## File Structure

```
chatty-commander/
├── webui/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # FastAPI application entry
│   │   │   ├── config.py               # WebUI configuration
│   │   │   ├── dependencies.py         # Dependency injection
│   │   │   ├── middleware.py           # CORS, auth middleware
│   │   │   ├── database.py             # Database connection
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py             # User model
│   │   │   │   ├── session.py          # Session model
│   │   │   │   └── audit.py            # Audit log model
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py             # Auth schemas
│   │   │   │   ├── config.py           # Config schemas
│   │   │   │   ├── service.py          # Service schemas
│   │   │   │   └── audio.py            # Audio schemas
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── auth.py          # Authentication endpoints
│   │   │   │   │   ├── config.py        # Configuration endpoints
│   │   │   │   │   ├── commands.py      # Commands management
│   │   │   │   │   ├── states.py        # States management
│   │   │   │   │   ├── service.py       # Service control
│   │   │   │   │   ├── models.py        # Models management
│   │   │   │   │   ├── audio.py         # Audio settings
│   │   │   │   │   ├── system.py        # System info
│   │   │   │   │   └── websocket.py     # WebSocket handlers
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py              # JWT handling
│   │   │   │   ├── security.py         # Security utilities
│   │   │   │   ├── config.py           # Core configuration
│   │   │   │   └── exceptions.py       # Custom exceptions
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chatty_service.py   # ChattyCommander integration
│   │   │   │   ├── config_service.py   # Configuration management
│   │   │   │   ├── audio_service.py    # Audio management
│   │   │   │   └── websocket_service.py # WebSocket management
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── file_utils.py       # File operations
│   │   │       ├── process_utils.py    # Process management
│   │   │       └── validation.py      # Data validation
│   │   ├── requirements.txt            # Python dependencies
│   │   ├── Dockerfile                  # Docker configuration
│   │   └── docker-compose.yml          # Docker Compose
│   ├── frontend/
│   │   ├── public/
│   │   │   ├── index.html
│   │   │   ├── favicon.ico
│   │   │   └── manifest.json
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── common/
│   │   │   │   │   ├── Layout.tsx       # Main layout component
│   │   │   │   │   ├── Header.tsx       # Header with navigation
│   │   │   │   │   ├── Sidebar.tsx      # Sidebar navigation
│   │   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   │   └── ErrorBoundary.tsx
│   │   │   │   ├── auth/
│   │   │   │   │   ├── LoginForm.tsx    # Login component
│   │   │   │   │   ├── ProtectedRoute.tsx
│   │   │   │   │   └── AuthProvider.tsx
│   │   │   │   ├── dashboard/
│   │   │   │   │   ├── Dashboard.tsx    # Main dashboard
│   │   │   │   │   ├── ServiceStatus.tsx
│   │   │   │   │   ├── QuickActions.tsx
│   │   │   │   │   └── SystemMetrics.tsx
│   │   │   │   ├── config/
│   │   │   │   │   ├── ConfigManager.tsx
│   │   │   │   │   ├── CommandsList.tsx
│   │   │   │   │   ├── CommandEditor.tsx
│   │   │   │   │   ├── StateManager.tsx
│   │   │   │   │   └── ModelManager.tsx
│   │   │   │   ├── audio/
│   │   │   │   │   ├── AudioSettings.tsx
│   │   │   │   │   ├── AudioLevelMeter.tsx
│   │   │   │   │   ├── DeviceSelector.tsx
│   │   │   │   │   └── VoiceTest.tsx
│   │   │   │   ├── service/
│   │   │   │   │   ├── ServiceControl.tsx
│   │   │   │   │   ├── LogViewer.tsx
│   │   │   │   │   └── ProcessMonitor.tsx
│   │   │   │   └── system/
│   │   │   │       ├── SystemInfo.tsx
│   │   │   │       └── HealthCheck.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts           # Authentication hook
│   │   │   │   ├── useWebSocket.ts      # WebSocket hook
│   │   │   │   ├── useConfig.ts         # Configuration hook
│   │   │   │   ├── useService.ts        # Service management hook
│   │   │   │   └── useAudio.ts          # Audio management hook
│   │   │   ├── services/
│   │   │   │   ├── api.ts               # API client
│   │   │   │   ├── auth.ts              # Auth service
│   │   │   │   ├── websocket.ts         # WebSocket client
│   │   │   │   └── storage.ts           # Local storage
│   │   │   ├── types/
│   │   │   │   ├── auth.ts              # Auth types
│   │   │   │   ├── config.ts            # Config types
│   │   │   │   ├── service.ts           # Service types
│   │   │   │   └── api.ts               # API types
│   │   │   ├── utils/
│   │   │   │   ├── constants.ts         # App constants
│   │   │   │   ├── helpers.ts           # Helper functions
│   │   │   │   └── validation.ts        # Form validation
│   │   │   ├── styles/
│   │   │   │   ├── theme.ts             # MUI theme
│   │   │   │   └── globals.css          # Global styles
│   │   │   ├── App.tsx                  # Main App component
│   │   │   ├── index.tsx                # Entry point
│   │   │   └── setupTests.ts            # Test setup
│   │   ├── package.json                 # Node dependencies
│   │   ├── tsconfig.json                # TypeScript config
│   │   ├── vite.config.ts               # Vite configuration
│   │   └── Dockerfile                   # Frontend Docker
│   ├── tests/
│   │   ├── backend/
│   │   │   ├── test_auth.py             # Auth tests
│   │   │   ├── test_config.py           # Config tests
│   │   │   ├── test_service.py          # Service tests
│   │   │   ├── test_websocket.py        # WebSocket tests
│   │   │   └── conftest.py              # Test fixtures
│   │   ├── frontend/
│   │   │   ├── components/
│   │   │   │   ├── Dashboard.test.tsx
│   │   │   │   ├── ConfigManager.test.tsx
│   │   │   │   └── ServiceControl.test.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.test.ts
│   │   │   │   └── useWebSocket.test.ts
│   │   │   └── services/
│   │   │       ├── api.test.ts
│   │   │       └── websocket.test.ts
│   │   └── e2e/
│   │       ├── auth.spec.ts             # E2E auth tests
│   │       ├── config.spec.ts           # E2E config tests
│   │       ├── service.spec.ts          # E2E service tests
│   │       └── playwright.config.ts     # Playwright config
│   ├── docs/
│   │   ├── api/
│   │   │   ├── README.md                # API documentation
│   │   │   └── examples/                # API examples
│   │   ├── frontend/
│   │   │   ├── README.md                # Frontend docs
│   │   │   └── components.md            # Component docs
│   │   └── deployment/
│   │       ├── docker.md                # Docker deployment
│   │       ├── nginx.md                 # Nginx configuration
│   │       └── ssl.md                   # SSL setup
│   ├── scripts/
│   │   ├── setup.sh                     # Setup script
│   │   ├── build.sh                     # Build script
│   │   ├── deploy.sh                    # Deployment script
│   │   └── test.sh                      # Test runner
│   ├── docker-compose.yml               # Full stack compose
│   ├── nginx.conf                       # Nginx configuration
│   └── README.md                        # WebUI documentation
└── webui_openapi_spec.yaml             # OpenAPI specification
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

#### Backend Setup

1. **Project Structure**

   ```bash
   mkdir -p webui/backend/app/{api/v1,core,models,schemas,services,utils}
   cd webui/backend
   python -m venv venv
   source venv/bin/activate
   ```

1. **Dependencies** (`requirements.txt`)

   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   pydantic==2.5.0
   python-jose[cryptography]==3.3.0
   python-multipart==0.0.6
   passlib[bcrypt]==1.7.4
   sqlalchemy==2.0.23
   alembic==1.13.0
   websockets==12.0
   pytest==7.4.3
   pytest-asyncio==0.21.1
   httpx==0.25.2
   ```

1. **Core FastAPI Application** (`app/main.py`)

   ```python
   from fastapi import FastAPI, WebSocket
   from fastapi.middleware.cors import CORSMiddleware
   from app.api.v1 import auth, config, service
   from app.core.config import settings

   app = FastAPI(
       title="ChattyCommander WebUI API",
       description="RESTful API for ChattyCommander web interface",
       version="1.0.0",
       openapi_url="/api/v1/openapi.json",
       docs_url="/api/v1/docs",
       redoc_url="/api/v1/redoc"
   )

   # CORS middleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_HOSTS,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Include routers
   app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
   app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
   app.include_router(service.router, prefix="/api/v1/service", tags=["service"])
   ```

#### Frontend Setup

1. **React Project**

   ```bash
   cd webui/frontend
   npm create vite@latest . -- --template react-ts
   npm install @mui/material @emotion/react @emotion/styled
   npm install @tanstack/react-query axios
   npm install react-router-dom @types/react-router-dom
   ```

1. **Basic App Structure** (`src/App.tsx`)

   ```typescript
   import React from 'react';
   import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
   import { ThemeProvider } from '@mui/material/styles';
   import CssBaseline from '@mui/material/CssBaseline';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import theme from './styles/theme';
   import Layout from './components/common/Layout';
   import Dashboard from './components/dashboard/Dashboard';
   import Login from './components/auth/LoginForm';

   const queryClient = new QueryClient();

   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         <ThemeProvider theme={theme}>
           <CssBaseline />
           <Router>
             <Routes>
               <Route path="/login" element={<Login />} />
               <Route path="/" element={<Layout />}>
                 <Route index element={<Dashboard />} />
               </Route>
             </Routes>
           </Router>
         </ThemeProvider>
       </QueryClientProvider>
     );
   }

   export default App;
   ```

### Phase 2: Authentication & Core API (Week 3-4)

#### Backend Authentication

1. **JWT Authentication** (`app/core/auth.py`)
1. **User Management** (`app/models/user.py`)
1. **Auth Endpoints** (`app/api/v1/auth.py`)
1. **Protected Routes** (`app/dependencies.py`)

#### Frontend Authentication

1. **Auth Context** (`src/components/auth/AuthProvider.tsx`)
1. **Login Form** (`src/components/auth/LoginForm.tsx`)
1. **Protected Routes** (`src/components/auth/ProtectedRoute.tsx`)
1. **API Client** (`src/services/api.ts`)

### Phase 3: Configuration Management (Week 5-6)

#### Backend Config API

1. **Config Schemas** (`app/schemas/config.py`)
1. **Config Service** (`app/services/config_service.py`)
1. **Config Endpoints** (`app/api/v1/config.py`)
1. **Commands Management** (`app/api/v1/commands.py`)

#### Frontend Config UI

1. **Config Manager** (`src/components/config/ConfigManager.tsx`)
1. **Commands List** (`src/components/config/CommandsList.tsx`)
1. **Command Editor** (`src/components/config/CommandEditor.tsx`)
1. **State Manager** (`src/components/config/StateManager.tsx`)

### Phase 4: Service Control & Monitoring (Week 7-8)

#### Backend Service API

1. **Service Integration** (`app/services/chatty_service.py`)
1. **Process Management** (`app/utils/process_utils.py`)
1. **Service Endpoints** (`app/api/v1/service.py`)
1. **System Info** (`app/api/v1/system.py`)

#### Frontend Service UI

1. **Service Control** (`src/components/service/ServiceControl.tsx`)
1. **Process Monitor** (`src/components/service/ProcessMonitor.tsx`)
1. **System Info** (`src/components/system/SystemInfo.tsx`)
1. **Dashboard** (`src/components/dashboard/Dashboard.tsx`)

### Phase 5: Real-time Features (Week 9-10)

#### Backend WebSocket

1. **WebSocket Service** (`app/services/websocket_service.py`)
1. **WebSocket Handlers** (`app/api/v1/websocket.py`)
1. **Real-time Events** (service status, audio levels, logs)

#### Frontend WebSocket

1. **WebSocket Hook** (`src/hooks/useWebSocket.ts`)
1. **Real-time Components** (status updates, audio meter)
1. **Log Viewer** (`src/components/service/LogViewer.tsx`)
1. **Audio Level Meter** (`src/components/audio/AudioLevelMeter.tsx`)

### Phase 6: Audio & Voice Features (Week 11-12)

#### Backend Audio API

1. **Audio Service** (`app/services/audio_service.py`)
1. **Audio Endpoints** (`app/api/v1/audio.py`)
1. **Voice Testing** (file upload, live testing)
1. **Model Management** (`app/api/v1/models.py`)

#### Frontend Audio UI

1. **Audio Settings** (`src/components/audio/AudioSettings.tsx`)
1. **Device Selector** (`src/components/audio/DeviceSelector.tsx`)
1. **Voice Test** (`src/components/audio/VoiceTest.tsx`)
1. **Model Manager** (`src/components/config/ModelManager.tsx`)

## Testing Strategy

### Backend Testing

1. **Unit Tests** (pytest)

   - API endpoints
   - Service classes
   - Authentication
   - Data validation

1. **Integration Tests**

   - Database operations
   - External service calls
   - WebSocket connections

1. **API Tests**

   - OpenAPI spec validation
   - Request/response testing
   - Error handling

### Frontend Testing

1. **Unit Tests** (Jest + React Testing Library)

   - Component rendering
   - Hook functionality
   - Utility functions

1. **Integration Tests**

   - API integration
   - WebSocket connections
   - Form submissions

1. **E2E Tests** (Playwright)

   - User workflows
   - Cross-browser testing
   - Mobile responsiveness

### Performance Testing

1. **Load Testing** (Locust)

   - API endpoint performance
   - WebSocket connection limits
   - Concurrent user handling

1. **Frontend Performance**

   - Bundle size optimization
   - Rendering performance
   - Memory usage

## Deployment Strategy

### Development Environment

```bash
# Backend
cd webui/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100

# Frontend
cd webui/frontend
npm run dev
```

### Production Deployment

1. **Docker Containers**

   - Backend: FastAPI + Uvicorn
   - Frontend: Nginx + React build
   - Database: PostgreSQL
   - Reverse Proxy: Nginx

1. **Docker Compose**

   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
      ports:
        - "8100:8100"
       environment:
         - DATABASE_URL=postgresql://user:pass@db:5432/chatty

     frontend:
       build: ./frontend
       ports:
         - "3000:80"

     db:
       image: postgres:15
       environment:
         - POSTGRES_DB=chatty
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=pass

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
   ```

## Security Considerations

1. **Authentication**

   - JWT tokens with expiration
   - Refresh token rotation
   - Rate limiting on auth endpoints

1. **Authorization**

   - Role-based access control
   - API endpoint permissions
   - Resource-level security

1. **Data Protection**

   - HTTPS enforcement
   - Input validation
   - SQL injection prevention
   - XSS protection

1. **Network Security**

   - CORS configuration
   - CSP headers
   - Secure WebSocket connections

## Success Metrics

1. **Functionality**

   - 100% feature parity with desktop GUI
   - All API endpoints functional
   - Real-time updates working

1. **Performance**

   - API response time \< 200ms
   - WebSocket latency \< 50ms
   - Frontend load time \< 3s

1. **Quality**

   - 90%+ test coverage
   - Zero critical security issues
   - Cross-browser compatibility

1. **User Experience**

   - Intuitive interface
   - Mobile responsive
   - Accessibility compliant

This implementation plan provides a comprehensive roadmap for developing a production-ready WebUI for ChattyCommander that mirrors all desktop functionality while adding web-specific enhancements like real-time monitoring and multi-user support.
