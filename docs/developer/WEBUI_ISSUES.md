# WebUI Issues Analysis

**Date:** 2026-02-20 (updated 2026-06-10)  
**Tested against:** Backend running on port 8100 with `--no-auth`

## Summary

Several frontend pages called API endpoints that didn't exist on the backend, causing 404 errors and degraded user experience. Most of these have since been implemented (audio devices, themes, preferences); the remaining gaps are system restart/shutdown and backup/restore.

## Issues Found

### 1. Endpoint Status

| Endpoint | Used By | Status |
|----------|---------|--------|
| `/api/audio/devices` | AudioSettingsPage.tsx | ✅ Implemented (`web/routes/audio.py`, also `/api/v1/audio/devices`) |
| `/api/audio/device` (POST) | AudioSettingsPage.tsx | ✅ Implemented (`web/routes/audio.py`) |
| `/api/voice/status` | apiService.js | ✅ Working |
| `/api/voice/start` | apiService.js | ✅ Working |
| `/api/voice/stop` | apiService.js | ✅ Working |
| `/api/themes` | apiService.js | ✅ Implemented (`web/routes/themes.py`) |
| `/api/theme` (GET/POST) | apiService.js | ✅ Implemented (`web/routes/themes.py`) |
| `/api/preferences` (GET/PUT) | apiService.js | ✅ Implemented (`web/routes/preferences.py`) |
| `/api/system/info` | apiService.js | ✅ Working |
| `/api/system/restart` | apiService.js | ❌ Missing |
| `/api/system/shutdown` | apiService.js | ❌ Missing |
| `/api/backup` | apiService.js | ❌ Missing |
| `/api/restore` | apiService.js | ❌ Missing |

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
| ConfigurationPage | ⚠️ Partial | Uses placeholder save function |
| AudioSettingsPage | ✅ Working | `/api/audio/devices` now implemented |
| PersonasPage | ⚠️ Partial | Context stats fail when advisors disabled |

## Next Steps

1. ~~Implement missing audio device endpoints~~ ✅ Done (`web/routes/audio.py`)
2. ~~Implement themes/preferences endpoints~~ ✅ Done (`web/routes/themes.py`, `web/routes/preferences.py`)
3. Decide whether to implement or drop the remaining missing endpoints: `/api/system/restart`, `/api/system/shutdown`, `/api/backup`, `/api/restore`
4. Implement ONNX file upload/download feature
5. Add proper error handling in frontend for any remaining missing endpoints
