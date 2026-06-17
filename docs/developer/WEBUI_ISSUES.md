# WebUI Issues Analysis

<<<<<<< HEAD
**Date:** 2026-02-20 (updated 2026-06-10)  
**Tested against:** Backend running on port 8100 with `--no-auth`
=======
**Date:** 2026-02-20 (initial)  
**Updated:** 2026-06-16 (endpoints fully wired + verified)  
**Tested against:** Backend running on port 8100 with `--no-auth` (and no_auth create_app paths)
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16

## Summary

Several frontend pages called API endpoints that didn't exist on the backend, causing 404 errors and degraded user experience. Most of these have since been implemented (audio devices, themes, preferences); the remaining gaps are system restart/shutdown and backup/restore.

## Issues Found

### 1. Endpoint Status

| Endpoint | Used By | Status |
|----------|---------|--------|
<<<<<<< HEAD
| `/api/audio/devices` | AudioSettingsPage.tsx | ✅ Implemented (`web/routes/audio.py`, also `/api/v1/audio/devices`) |
| `/api/audio/device` (POST) | AudioSettingsPage.tsx | ✅ Implemented (`web/routes/audio.py`) |
| `/api/voice/status` | apiService.js | ✅ Working |
| `/api/voice/start` | apiService.js | ✅ Working |
| `/api/voice/stop` | apiService.js | ✅ Working |
| `/api/themes` | apiService.js | ✅ Implemented (`web/routes/themes.py`) |
| `/api/theme` (GET/POST) | apiService.js | ✅ Implemented (`web/routes/themes.py`) |
| `/api/preferences` (GET/PUT) | apiService.js | ✅ Implemented (`web/routes/preferences.py`) |
=======
| `/api/audio/devices` | AudioSettingsPage.tsx / ConfigurationPage.tsx | ✅ Working (GET/POST; + /api/v1/ variants; pyaudio or safe mocks; persists to config) |
| `/api/voice/status` | apiService.js | ✅ Working |
| `/api/voice/start` | apiService.js | ✅ Working |
| `/api/voice/stop` | apiService.js | ✅ Working |
| `/api/themes` | apiService.js | ✅ Working (GET reports current from config when wired; POST sets + persists) |
| `/api/theme` | apiService.js | ✅ Working |
| `/api/preferences` | apiService.js | ✅ Working (GET + PUT update; persists via config mgr) |
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
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
<<<<<<< HEAD
| ConfigurationPage | ⚠️ Partial | Uses placeholder save function |
| AudioSettingsPage | ✅ Working | `/api/audio/devices` now implemented |
=======
| ConfigurationPage | ⚠️ Partial | Audio device + theme/prefs now functional via backend (save still mixes placeholder in places) |
| AudioSettingsPage | ✅ Working (ref: ConfigurationPage) | (Was listed; now served by /api/audio/* in audio.py + system prefs) |
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
| PersonasPage | ⚠️ Partial | Context stats fail when advisors disabled |

## Next Steps

<<<<<<< HEAD
1. ~~Implement missing audio device endpoints~~ ✅ Done (`web/routes/audio.py`)
2. ~~Implement themes/preferences endpoints~~ ✅ Done (`web/routes/themes.py`, `web/routes/preferences.py`)
3. Decide whether to implement or drop the remaining missing endpoints: `/api/system/restart`, `/api/system/shutdown`, `/api/backup`, `/api/restore`
4. Implement ONNX file upload/download feature
5. Add proper error handling in frontend for any remaining missing endpoints
=======
1. ~~Implement missing audio device endpoints~~ (DONE: /api/audio/devices + /api/audio/device + v1 variants + device selection persist to config; audio.py; compatible with AudioSettingsPage/ConfigurationPage.tsx direct fetches + apiService.js)
2. ~~Implement ONNX file upload/download feature~~ (DONE: /api/v1/models/files GET, /upload, /download/{name}, /files/{name} DELETE; models.py; also legacy audio fixed)
3. ~~Add themes/preferences + system control endpoints~~ (DONE: /api/themes + current reporting, /api/theme, /api/preferences (GET/PUT), /api/backup, /api/restore (config snapshot/apply), /api/system/restart, /api/system/shutdown; extended system.py w/ Pydantic models + auth notes; fully wired in web_mode.py _create_app (main prod path) + server.create_app; persistence via get_config_manager to live Config; stubs are practical for UX; verified no 404s)
4. Add proper error handling in frontend for missing endpoints (still recommended)
5. Add fallback/mock data in frontend when endpoints unavailable (still recommended)

**Implementation note (2026-06):** Completed remaining wiring + enhancements for the "DONE" items in prior note. Key changes:
- src/chatty_commander/web/routes/system.py: added ThemeInfo/ThemeSetRequest/PreferencesResponse/ActionResponse (minimal Pydantic per patterns in core/voice), get_themes() now reads+reports "current" from cfg.ui.theme (and persists on set), improved backup/restore to snapshot/apply config data, added detailed docstrings+auth protection notes for restart/shutdown (work with --no-auth + middleware), response_models on several.
- src/chatty_commander/web/web_mode.py: fixed include_system_routes(...) call to pass get_config_manager=lambda: self.config_manager (was missing, unlike audio include and server.py path; now themes/prefs/backup etc persist in real WebModeServer runs used by CLI/web).
- server.py create_app already correctly passed cfg_getter (kept compatible).
- audio.py: already complete (mocks when no pyaudio; no new dep; both legacy /api/ + /v1/).
- Verified: clean `uv run` imports, full TestClient on create_app (no_auth) hits all 12 endpoints @200, persistence exercised (save_config), smoke test passes, both app creators.
- Follows FastAPI APIRouter patterns, no signature breaks, compatible with existing middleware.
See routes/audio.py, routes/system.py, web/web_mode.py, web/server.py, tests/smoke/test_core_routes.py, and updated integration tests. All gaps from original table now ✅ and frontend UX improved (no more 404s on these calls).

**Playwright E2E coverage (2026-06-17):** Added browser-driven tests in tests/e2e/test_web_e2e.py: test_state_via_playwright, test_personas_via_playwright, test_commands_via_playwright (using page.evaluate fetch against live inproc server). Complements existing WS/config/themes/prefs. Helps verify dashboard/state, PersonasPage, command flows. TS e2e (dashboard.spec.ts etc) continue with mocks for UI render/UX. Added test_dashboard_spa_renders_via_playwright for full SPA /dashboard load + UI shell render check using playwright navigation + content (exercises React dashboard journey end-to-end with live server).
>>>>>>> fix/syntax-rot-webui-tests-2026-06-16
