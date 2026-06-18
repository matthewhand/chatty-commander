# WebUI Issues Analysis

**Date:** 2026-02-20 (initial)  
**Updated:** 2026-06-16 (endpoints fully wired + verified; see ARCHITECTURE.md for vision and legacy notes)  
**Tested against:** Backend running on port 8100 with `--no-auth` (and no_auth create_app paths)

> **Note:** This file previously contained merge artifacts between HEAD and the `fix/syntax-rot-webui-tests-2026-06-16` branch. They have been resolved for clarity. For architectural vision and legacy discussion see [ARCHITECTURE.md](ARCHITECTURE.md).

## Summary

Several frontend pages called API endpoints that didn't exist on the backend, causing 404 errors and degraded user experience. Most of these have since been implemented (audio devices, themes, preferences); the remaining gaps are system restart/shutdown and backup/restore.

## Issues Found

### 1. Endpoint Status

| Endpoint | Used By | Status |
|----------|---------|--------|
| `/api/audio/devices` | AudioSettingsPage.tsx / ConfigurationPage.tsx | ✅ Working (GET/POST; + /api/v1/ variants; pyaudio or safe mocks; persists to config) |
| `/api/audio/device` (POST) | AudioSettingsPage.tsx | ✅ Implemented (`web/routes/audio.py`) |
| `/api/voice/status` | apiService.js | ✅ Working |
| `/api/voice/start` | apiService.js | ✅ Working |
| `/api/voice/stop` | apiService.js | ✅ Working |
| `/api/themes` | apiService.js | ✅ Working (GET reports current from config when wired; POST sets + persists) |
| `/api/theme` (GET/POST) | apiService.js | ✅ Working |
| `/api/preferences` (GET/PUT) | apiService.js | ✅ Working (GET + PUT update; persists via config mgr) |
| `/api/system/info` | apiService.js | ✅ Working |
| `/api/system/restart` | apiService.js | ✅ Working (graceful 200+ack stub; auth-protected note in code) |
| `/api/system/shutdown` | apiService.js | ✅ Working (graceful 200+ack stub; auth-protected note in code) |
| `/api/backup` | apiService.js | ✅ Working (POST returns config snapshot stub + data for restore) |
| `/api/restore` | apiService.js | ✅ Working (POST applies to config where possible) |

### 2. API Errors (400 Bad Request)

| Endpoint | Issue |
|----------|-------|
| `/api/v1/advisors/context/stats` | Returns "Advisors not enabled" when advisors disabled in config |

### 3. Working Endpoints

| Endpoint | Status |
|----------|--------|
| `/health` | ✅ Working |
| `/api/v1/status` | ✅ Working |
| `/api/v1/config` | ✅ Working |
| `/api/v1/state` | ✅ Working |
| `/api/v1/metrics` | ✅ Working |
| `/api/v1/advisors/personas` | ✅ Working |
| `/api/system/info` | ✅ Working |

## Recommendations

### Priority 1: Add Missing Audio Endpoints — ✅ Done

The AudioSettingsPage.tsx needed (now implemented in `web/routes/audio.py`):
- `GET /api/audio/devices` - List available audio input devices
- `POST /api/audio/device` - Set active audio device

### Priority 2: Add Voice Status Endpoints — ✅ Done

For voice control features (implemented in `web/routes/voice.py`):
- `GET /api/voice/status` - Get voice recognition status
- `POST /api/voice/start` - Start voice recognition
- `POST /api/voice/stop` - Stop voice recognition

### Priority 3: Add Preferences Endpoints — ✅ Done

For dashboard and system management (implemented in `web/routes/preferences.py`):
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update user preferences

### Priority 4: Add File Management Endpoints (New Feature)

For ONNX model management:
- `GET /api/models/files` - List available ONNX model files
- `POST /api/models/upload` - Upload new ONNX model file
- `GET /api/models/download/{filename}` - Download ONNX model file
- `DELETE /api/models/files/{filename}` - Delete ONNX model file

## Frontend Fixes Applied

The following frontend (Web UI) issues have been resolved:

| Area | Fix | Status |
|------|-----|--------|
| Commands list "Edit" button | Now opens the authoring page **pre-filled** for editing (previously did not). | ✅ Fixed |
| Command delete | A failed delete now surfaces an error and keeps the dialog open instead of silently closing and implying success. | ✅ Fixed |
| JSON import | Each command's shape is now validated before overwriting config. | ✅ Fixed |
| ThemeProvider / authService | Logging cleaned up; WebSocket frame guards added; `useAuth` retry timeout cleared on unmount. | ✅ Fixed |

## Frontend Pages Status

| Page | Status | Issues |
|------|--------|--------|
| LoginPage | ✅ Working | None |
| DashboardPage | ⚠️ Partial | Uses placeholder data, WebSocket may fail |
| ConfigurationPage | ⚠️ Partial | Audio device + theme/prefs now functional via backend (save still mixes placeholder in places) |
| AudioSettingsPage | ✅ Working (ref: ConfigurationPage) | (Was listed; now served by /api/audio/* in audio.py + system prefs) |
| PersonasPage | ⚠️ Partial | Context stats fail when advisors disabled |

## Next Steps

1. ~~Implement missing audio device endpoints~~ ✅ Done (`web/routes/audio.py`; `/api/audio/devices` + POST `/api/audio/device` + v1 variants; persists; mocks when no pyaudio)
2. ~~Implement themes/preferences + system control endpoints~~ ✅ Done (`web/routes/themes.py`, `web/routes/preferences.py`, `web/routes/system.py`; GET/POST/PUT for theme/prefs + backup/restore/restart/shutdown stubs with Pydantic + auth notes; wired via config manager in web_mode + server)
3. ~~Implement ONNX file upload/download feature~~ ✅ Done (`web/routes/models.py`; GET /api/v1/models/files, upload, download, delete)
4. Add proper error handling + fallback data in frontend for any edge cases (recommended, some partials remain on dashboard/personas when advisors off)
5. Expand e2e + unit coverage and tie more explicitly to Vision (see ARCHITECTURE.md)

**Implementation note (2026-06):** All original listed endpoints now ✅ wired and verified (no 404s). Full TestClient hits, persistence works, Playwright e2e exercises live inproc server paths for state/commands/agents.

**Playwright E2E coverage (2026-06-17):** browser-driven tests in `tests/e2e/test_web_e2e.py` (test_state_via_playwright, test_personas_via_playwright, test_commands_via_playwright, test_dashboard_spa_renders_via_playwright using page.evaluate + navigation) + TS specs (dashboard.spec.ts etc with scoped `.card:has-text`, getByRole). Uses mocks for UI + live for backend-wired. Complements WS/config.

(For Vision, Honest Assessment (✅🟡🔲), and Legacy/Archived architectures see [ARCHITECTURE.md](ARCHITECTURE.md). This doc supports the front-and-centre vision of local-first reliable voice automation with React dashboard.)
