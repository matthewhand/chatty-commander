# Production Readiness Roadmap

**Current Version:** 0.2.0 (Beta)  
**Target:** 1.0.0 Production Release  
**Last Updated:** 2026-02-20

## Executive Summary

ChattyCommander is currently at version 0.2.0 with solid foundations:
- 95 Python source files (~18K lines)
- 221 tests collected
- CI/CD pipeline with GitHub Actions
- Docker support with Redis, PostgreSQL, Nginx
- Security features (JWT, rate limiting, security headers)
- Monitoring (health checks, Prometheus metrics)

This document outlines the work required to achieve production readiness.

---

## Phase 1: Security Hardening (Priority: Critical)

### 1.1 Secrets Management
- [ ] **Remove hardcoded secrets** from codebase
  - Audit all files for embedded API keys, tokens, passwords
  - Use environment variables or secret management (HashiCorp Vault, AWS Secrets Manager)
- [ ] **Implement secrets validation** at startup
  - Fail fast if required secrets are missing
  - Add `SECRETS_VALIDATION=true` config option
- [ ] **Add `.env.schema`** file documenting all required environment variables

### 1.2 Authentication & Authorization
- [ ] **Complete JWT implementation**
  - Token refresh mechanism
  - Token revocation/blacklist for logout
  - Configurable token expiration per environment
- [ ] **Add role-based access control (RBAC)**
  - Admin, User, ReadOnly roles
  - Permission checks on sensitive endpoints
- [ ] **Implement API key authentication** for service-to-service communication

### 1.3 Input Validation & Sanitization
- [ ] **Add request validation middleware**
  - JSON schema validation for all API inputs
  - SQL injection prevention (parameterized queries)
  - XSS prevention (content sanitization)
- [ ] **Rate limiting per user/IP**
  - Configurable limits per endpoint
  - Redis-backed distributed rate limiting

### 1.4 Security Auditing
- [ ] **Enable CodeQL scanning** in CI (already have `.github/workflows/codeql.yml`)
- [ ] **Add dependency scanning** (pip-audit, safety)
- [ ] **Add SAST tool** (Bandit already in dev dependencies)
- [ ] **Penetration testing** checklist

---

## Phase 2: Reliability & Resilience (Priority: High)

### 2.1 Error Handling
- [ ] **Standardize error responses**
  - Consistent JSON error format: `{error, code, details, request_id}`
  - HTTP status code mapping
- [ ] **Add circuit breaker** for external services
  - LLM API calls
  - Database connections
  - Redis connections
- [ ] **Implement graceful degradation**
  - Fallback responses when LLM unavailable
  - Cache-first strategy for config

### 2.2 Database & Persistence
- [ ] **Add database migrations** (Alembic)
  - Version-controlled schema changes
  - Rollback capability
- [ ] **Connection pooling**
  - Configure SQLAlchemy pool size
  - Add connection health checks
- [ ] **Data backup strategy**
  - Automated PostgreSQL backups
  - Point-in-time recovery

### 2.3 Observability
- [ ] **Structured logging**
  - JSON log format for production
  - Log levels per environment
  - Request ID tracing
- [ ] **Distributed tracing** (OpenTelemetry)
  - Trace requests across services
  - Performance bottleneck identification
- [ ] **Alerting rules**
  - Prometheus AlertManager configuration
  - PagerDuty/OpsGenie integration

---

## Phase 3: Performance & Scalability (Priority: High)

### 3.1 Caching Strategy
- [ ] **Implement Redis caching**
  - Configuration caching
  - Session storage
  - LLM response caching (with TTL)
- [ ] **Cache invalidation**
  - Event-based invalidation
  - TTL-based expiration

### 3.2 Async Processing
- [ ] **Add task queue** (Celery or RQ)
  - Background LLM processing
  - Email notifications
  - Report generation
- [ ] **WebSocket connection management**
  - Connection pooling
  - Heartbeat mechanism
  - Reconnection logic

### 3.3 Load Testing
- [ ] **Performance benchmarks**
  - Response time SLAs
  - Throughput targets
- [ ] **Load test suite**
  - Locust or k6 scripts
  - CI integration for performance regression

---

## Phase 4: Testing & Quality (Priority: High)

### 4.1 Test Coverage
- [ ] **Increase coverage to 90%+**
  - Current: ~85% (claimed)
  - Add missing edge case tests
  - Integration tests for all API endpoints
- [ ] **Add contract tests**
  - OpenAPI schema validation
  - Consumer-driven contracts for external APIs

### 4.2 End-to-End Testing
- [ ] **Expand Playwright tests**
  - Critical user journeys
  - Cross-browser testing
  - Mobile responsiveness
- [ ] **Add API integration tests**
  - Test against real database
  - Test with mocked external services

### 4.3 Chaos Engineering
- [ ] **Add failure injection tests**
  - Database failure simulation
  - Network latency injection
  - Service unavailability handling

---

## Phase 5: Deployment & Operations (Priority: Medium)

### 5.1 Container Hardening
- [ ] **Docker security**
  - Non-root user in container
  - Read-only filesystem
  - Security scanning (Trivy)
- [ ] **Multi-stage builds**
  - Smaller production images
  - Separate build and runtime stages

### 5.2 Kubernetes Ready
- [ ] **Add Kubernetes manifests**
  - Deployment, Service, ConfigMap, Secret
  - HorizontalPodAutoscaler
  - PodDisruptionBudget
- [ ] **Health probes**
  - Liveness probe
  - Readiness probe
  - Startup probe

### 5.3 CI/CD Improvements
- [ ] **Add staging environment**
  - Automatic deployment on main merge
  - Production deployment on release tags
- [ ] **Rollback automation**
  - Blue-green deployment
  - Canary releases

---

## Phase 6: Documentation & Support (Priority: Medium)

### 6.1 User Documentation
- [ ] **Installation guide**
  - Platform-specific instructions
  - Dependency requirements
- [ ] **Configuration reference**
  - All config options documented
  - Example configurations
- [ ] **Troubleshooting guide**
  - Common issues and solutions
  - Debug mode instructions

### 6.2 API Documentation
- [ ] **OpenAPI spec completeness**
  - All endpoints documented
  - Request/response examples
  - Error response documentation
- [ ] **Interactive API explorer**
  - Swagger UI improvements
  - Authentication in docs

### 6.3 Operational Runbooks
- [ ] **Incident response**
  - Common incident scenarios
  - Escalation procedures
- [ ] **Maintenance procedures**
  - Backup/restore
  - Database migrations
  - Configuration updates

---

## Phase 7: Feature Completeness (Priority: Low)

### 7.1 Core Features
- [ ] **Voice pipeline stability**
  - Wake word accuracy metrics
  - Fallback to text input
- [ ] **LLM integration**
  - Multiple provider support
  - Model switching at runtime
  - Cost tracking

### 7.2 User Experience
- [ ] **WebUI polish**
  - Error states
  - Loading states
  - Offline support
- [ ] **Desktop app**
  - Auto-update mechanism
  - System tray integration
  - Native notifications

---

## Metrics & Success Criteria

### Security
- [ ] Zero critical/high vulnerabilities in dependencies
- [ ] All secrets externalized
- [ ] Security scan passing in CI

### Reliability
- [ ] 99.9% uptime target
- [ ] Mean Time To Recovery (MTTR) < 15 minutes
- [ ] Zero data loss on failure

### Performance
- [ ] API response time < 200ms (p95)
- [ ] WebSocket latency < 100ms
- [ ] Support 1000 concurrent users

### Quality
- [ ] Test coverage > 90%
- [ ] Zero critical bugs
- [ ] All E2E tests passing

---

## Recommended Next Steps (Immediate)

1. **Security Audit** (Week 1-2)
   - Run `bandit -r chatty_commander/`
   - Run `pip-audit` and fix vulnerabilities
   - Externalize all secrets

2. **Test Coverage** (Week 2-3)
   - Run `pytest --cov=chatty_commander --cov-report=html`
   - Identify and fill coverage gaps
   - Add integration tests

3. **Error Handling** (Week 3-4)
   - Standardize error responses
   - Add circuit breakers
   - Implement graceful degradation

4. **Documentation** (Week 4-5)
   - Complete API documentation
   - Write troubleshooting guide
   - Create operational runbooks

5. **Performance Testing** (Week 5-6)
   - Set up load testing infrastructure
   - Establish performance baselines
   - Optimize bottlenecks

---

## Phase 8: Deprecated & Removed Features

### 8.1 Advanced Avatar System / Avatar GUI
- The 3D Avatar GUI (`src/chatty_commander/gui.py` and `/avatar/ws` endpoints) has been **removed**. The progressive web UI is the singular visual interface moving forward.

### 8.2 Desktop Native Experience
- Standalone GUI desktop apps are discouraged in favor of the WebUI.

---

## Version Milestones

| Version | Target Date | Focus Area |
|---------|-------------|------------|
| 0.3.0 | Q2 2026 | Security Hardening |
| 0.4.0 | Q3 2026 | Reliability & Resilience |
| 0.5.0 | Q3 2026 | Performance & Scalability |
| 0.6.0 | Q4 2026 | Testing & Quality |
| 0.7.0 | Q4 2026 | Deployment & Operations |
| 0.8.0 | Q1 2027 | Documentation & Support |
| 0.9.0 | Q1 2027 | Feature Completeness |
| 1.0.0 | Q2 2027 | Production Release |

---

## Conclusion

ChattyCommander has a solid foundation but requires focused effort in security, reliability, and operational readiness before production deployment. The roadmap above provides a structured approach to achieving production readiness.

**Key Investment Areas:**
1. Security hardening (non-negotiable for production)
2. Error handling and resilience
3. Comprehensive testing
4. Operational documentation

**Quick Wins:**
- Externalize secrets
- Add circuit breakers
- Improve error messages
- Complete API documentation

---

## Feature Backlog (Roadmap Items)

This section captures all identified unfinished features, stubs, and deferred work discovered during codebase analysis. Items are organized by domain.

### LLM & AI Integration

- **MCP/Handoffs support** (`src/chatty_commander/advisors/providers.py`): `mcp_servers` and `handoffs` are empty lists; needs real MCP server configuration and agent handoff routing.
- **Provider-specific prompt formatting** (`src/chatty_commander/advisors/prompting.py`): `build_prompt()` currently produces a generic envelope; needs provider-specific formatting for OpenAI, Anthropic, Ollama, and other backends.
- **LLM-powered NL blueprint parser** (`src/chatty_commander/web/routes/agents.py`): natural language agent blueprint parser uses naive keyword heuristics; needs a real LLM call for accurate intent extraction.
- **LLM-powered avatar animation classifier** (`src/chatty_commander/web/routes/avatar_selector.py`): animation state classifier uses keyword matching; needs an LLM-based classifier for higher accuracy.
- **Multiple LLM providers**: runtime model switching, cost tracking across OpenAI/Anthropic/Ollama/local models.
- **`generate()` kwargs expansion** (`src/chatty_commander/advisors/providers.py`): kwargs are accepted but unused; needs real provider-specific parameter passthrough (temperature, max_tokens, stop sequences, etc.).

### Web API & Endpoints

- **Missing WebUI API endpoints** (documented in `docs/developer/WEBUI_ISSUES.md`):
  - `GET /api/audio/devices` — audio device enumeration
  - `GET/POST /api/voice/status`, `/api/voice/start`, `/api/voice/stop` — voice pipeline control
  - `GET /api/themes`, `GET/POST /api/theme` — theme management
  - `GET/PUT /api/preferences` — user preferences
  - `GET /api/system/info`, `POST /api/system/restart`, `POST /api/system/shutdown` — system management
  - `POST /api/backup`, `POST /api/restore` — backup/restore
- **Real database health check** (`src/chatty_commander/web/routes/core.py`): health endpoint returns hardcoded `"not_configured"`; needs real DB connectivity check.
- **Response time metrics** (`src/chatty_commander/web/routes/core.py`): metrics endpoint always returns `0.0` for average response time; needs real measurement instrumentation.
- **Node.js bridge processing** (`src/chatty_commander/web/web_mode.py`): bridge endpoint only echoes events back; needs real Node.js bridge event processing logic.

### Agent & Orchestration

- **Agent blueprint persistence** (`src/chatty_commander/web/routes/agents.py`): blueprints stored in in-memory dict `_STORE`; needs database persistence (PostgreSQL/SQLite) with proper lifecycle management.
- **Agent handoff integration** (`src/chatty_commander/web/routes/agents.py`): handoff endpoint returns a stub acknowledgement; needs integration with `thinking_state` and `avatar_ws` for real handoff coordination.
- **Avatar-to-agent ID mapping** (`src/chatty_commander/web/routes/avatar_ws.py`): WebSocket handler has no agent-to-avatar ID mapping; needs a registry to correlate avatar sessions with agent identities.
- **Wake word → advisor/voice mode** (`src/chatty_commander/app/orchestrator.py`): wake word detection only triggers commands; needs to activate voice input or advisor mode as an alternative response path.

### Browser & Tool Integration

- **Real browser analyst tool** (`src/chatty_commander/advisors/tools/browser_analyst.py` and `src/chatty_commander/tools/browser_analyst.py`): both return hardcoded deterministic responses; needs real HTTP fetch, content extraction, and LLM summarization with allowlists and timeouts.
- **Custom message UI notifications** (`src/chatty_commander/app/command_executor.py`): `_execute_custom_message()` only logs the message; needs UI notification dispatch (WebSocket push or system notification).

### Observability & Metrics

- **Wire metrics module to server** (`src/chatty_commander/obs/metrics.py`): module exists but is not connected to the running server by default; needs integration with web server startup so middleware and router are installed automatically.
- **Voice self-test tuning application** (`src/chatty_commander/voice/self_test.py`): tuning recommendations are logged but never applied; needs an auto-apply or user-confirmation flow to act on the recommendations.

### Voice & Wake Word

- **Real ONNX wake word models** (`src/chatty_commander/app/default_config.py`): `.onnx` files are text stub files created for development/testing; needs real trained ONNX wake word models for production use.
- **Voice pipeline stability**: wake word accuracy metrics, fallback-to-text when voice recognition fails.

### Auth & Docs

- **`enable_no_auth_docs()` implementation** (`src/chatty_commander/web/auth.py`): function is currently a no-op; needs a real toggle for disabling auth on API docs endpoints in development mode (FastAPI does not support toggling `docs_url`/`redoc_url` after init, so manual route attachment is required).

### WebUI Polish

- **Dashboard real data** (`docs/developer/WEBUI_ISSUES.md`): DashboardPage uses placeholder data; needs real WebSocket data binding for live metrics and status.
- **Configuration page save** (`docs/developer/WEBUI_ISSUES.md`): ConfigurationPage uses a placeholder save function; needs a real API call to persist configuration changes.
- **Error states, loading states, offline support**: WebUI needs proper UX for all failure modes including network errors, server unavailability, and partial data.
