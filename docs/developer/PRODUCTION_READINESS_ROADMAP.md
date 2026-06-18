# Production Readiness Roadmap (moved)

This document has been consolidated into the single canonical roadmap at the
repository root: [`ROADMAP.md`](../../ROADMAP.md).

- Still-relevant open items were carried over (see "P2 — Production hardening
  (carried from PRODUCTION_READINESS_ROADMAP)" and the P0/P1 sections there).
- Obsolete items (Kubernetes manifests, Celery/Redis task queue, Alembic
  migrations, PagerDuty alerting, the already-completed avatar-GUI removal
  notes) were dropped after verification against the current tree.

This file is kept only so existing links don't break. Please update any
references to point at [`ROADMAP.md`](../../ROADMAP.md).

---

**Historical note (archived content):** The previous version of this file described the state around 0.2.0 beta with foundations in security, syntax cleanup, WebUI wiring, and test expansion. For current status see the root ROADMAP.md. Legacy architectural discussions have moved to the ARCHITECTURE.md "Legacy and Archived Architectures" section.

---

## Phase 1: Security Hardening (Priority: Critical)

**Audit Summary (Security & Audit Subagent - 2026-06-16; follow-up 2026-06-16):** Tools re-run successfully (bandit/pip-audit/safety + QA agents). See detailed findings in this edit + `.env.schema`. Secrets: clean. **Syntax rot eliminated (0 broken files in src+tests via AST/py_compile; multiple direct + 6+ subagent sweeps on 40+ files including config, web/, ai/, voice/, app/, tools/, avatars/, utils/)**. SAST (bandit) now fully runnable on src. Deps: many vulns (report in pip-audit/safety; non-prod ignore list recommended). Auth: API key present + rate limit partial. JWT incomplete. Fixes applied: .env.schema created, docs/rate limit notes updated, Makefile improved, .gitignore enhanced. WebUI priority endpoints wired (audio/themes/prefs/backup/restart etc + registration fix). Update last-updated date and re-audit after syntax fixes.

### 1.1 Secrets Management
- [x] **Remove hardcoded secrets** from codebase  *(Phase 1 Security Audit Subagent, 2026-06-16: Full audit via grep + SecurityAuditAgent + manual review of src/, config/, docker*, .env*, tests. ZERO production secrets/tokens/keys found. Only placeholders in .env.example, example code, test mocks, and docker defaults with ${VAR:-...} . See SECURITY.md for generation.)*
  - Audit all files for embedded API keys, tokens, passwords
  - Use environment variables or secret management (HashiCorp Vault, AWS Secrets Manager)
- [ ] **Implement secrets validation** at startup
  - Fail fast if required secrets are missing
  - Add `SECRETS_VALIDATION=true` config option
- [x] **Add `.env.schema`** file documenting all required environment variables  *(Created .env.schema at root; references all from .env.example + code/SECURITY.md. Recommend startup validation using it.)*

### 1.2 Authentication & Authorization
- [ ] **Complete JWT implementation**
  - Token refresh mechanism
  - Token revocation/blacklist for logout
  - Configurable token expiration per environment
  *(Note from Phase1 audit: pyjwt dep present; API-key auth + middleware fully functional in web/middleware/auth.py (X-API-Key, constant_time_compare, no_auth support, anti-traversal). Legacy/broken code in web/auth.py and mangled shims in server/web_mode. No visible refresh/revoke/blacklist or JWT issuance endpoints in current tree. Frontend login exists but server auth is primarily API-key. Roadmap: either complete JWT or document API-key as primary.)*
- [ ] **Add role-based access control (RBAC)**
  - Admin, User, ReadOnly roles
  - Permission checks on sensitive endpoints
- [ ] **Implement API key authentication** for service-to-service communication

### 1.3 Input Validation & Sanitization
- [ ] **Add request validation middleware**
  - JSON schema validation for all API inputs
  - SQL injection prevention (parameterized queries)
  - XSS prevention (content sanitization)
- [x] **Rate limiting per user/IP** *(Partial: Basic in-memory RateLimitMiddleware implemented in web/web_mode.py (60/min default, headers, proxy-aware IP). Not per-endpoint configurable or Redis-backed yet. See updated builder.py docs and SECURITY.md nginx example. Low-hanging: wire into create_app.)*
  - Configurable limits per endpoint
  - Redis-backed distributed rate limiting

### 1.4 Security Auditing
- [ ] **Enable CodeQL scanning** in CI (already have `.github/workflows/codeql.yml`)
- [x] **Add dependency scanning** (pip-audit, safety)  *(Implemented in dev+security groups in pyproject.toml; Makefile updated; QA DependencyAuditAgent + direct runs now functional. Run: `uv run --group security pip-audit` / `safety check`. Note: 50-75 vulns typically reported (mix runtime/dev); track in CI with ignore lists for non-prod.)*
- [x] **Add SAST tool** (Bandit already in dev dependencies)  *(Bandit in security group; runs via `uv run --group security bandit -r src/...`. Only 4 LOW issues found on scan (subprocess git, bare except). However, ~65 files skipped due to AST syntax errors in current src/ (see below).)*
- [ ] **Penetration testing** checklist
- [ ] **Run QA security/dependency agents** successfully (previously ERROR in qa_report.json; now pass when using correct uv groups)

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
- [ ] **Audio Output Support**
  - Select output device
  - Text-to-Speech playback
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
   - Run `uv run --group security bandit -r src/chatty_commander/`
   - Run `uv run --group security pip-audit` and `safety check` and fix/ignore vulns (75+ reported; prioritize runtime like urllib3, starlette, python-multipart, pyjwt)
   - Externalize all secrets (audit complete: none found in code)
   - **Critical finding (discovered during audit):** 65+ src/ files have Python syntax errors (broken indents, mangled docstrings from prior edits) causing SAST skips and potential runtime issues from source. .pyc in .venv may mask. Fix syntax before full prod readiness. Re-run full bandit post-fix.
   - Created `.env.schema`; basic rate limiting exists (in-mem).

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

(See [ARCHITECTURE.md](ARCHITECTURE.md) for Vision, honest ✅🟡🔲 assessment of built vs remaining, and the Archived/Legacy Architectures section.)
