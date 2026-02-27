# WebUI Issues Analysis

**Date:** 2026-02-20  
**Tested against:** Backend running on port 8100 with `--no-auth`

## Summary

Several frontend pages call API endpoints that don't exist on the backend, causing 404 errors and degraded user experience.

## Issues Found

### 1. Missing API Endpoints (404 Not Found)

| Endpoint | Used By | Status |
|----------|---------|--------|
| `/api/audio/devices` | AudioSettingsPage.tsx | ❌ Missing |
| `/api/voice/status` | apiService.js | ❌ Missing |
| `/api/voice/start` | apiService.js | ❌ Missing |
| `/api/voice/stop` | apiService.js | ❌ Missing |
| `/api/themes` | apiService.js | ❌ Missing |
| `/api/theme` | apiService.js | ❌ Missing |
| `/api/preferences` | apiService.js | ❌ Missing |
| `/api/system/info` | apiService.js | ❌ Missing |
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

## Recommendations

### Priority 1: Add Missing Audio Endpoints

The AudioSettingsPage.tsx needs:
- `GET /api/audio/devices` - List available audio input/output devices
- `POST /api/audio/device` - Set active audio device

### Priority 2: Add Voice Status Endpoints

For voice control features:
- `GET /api/voice/status` - Get voice recognition status
- `POST /api/voice/start` - Start voice recognition
- `POST /api/voice/stop` - Stop voice recognition

### Priority 3: Add System Info Endpoints

For dashboard and system management:
- `GET /api/system/info` - Get system information (CPU, memory, disk)
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update user preferences

### Priority 4: Add File Management Endpoints (New Feature)

For ONNX model management:
- `GET /api/models/files` - List available ONNX model files
- `POST /api/models/upload` - Upload new ONNX model file
- `GET /api/models/download/{filename}` - Download ONNX model file
- `DELETE /api/models/files/{filename}` - Delete ONNX model file

## Frontend Pages Status

| Page | Status | Issues |
|------|--------|--------|
| LoginPage | ✅ Working | None |
| DashboardPage | ⚠️ Partial | Uses placeholder data, WebSocket may fail |
| ConfigurationPage | ⚠️ Partial | Uses placeholder save function |
| AudioSettingsPage | ❌ Broken | Calls missing `/api/audio/devices` |
| PersonasPage | ⚠️ Partial | Context stats fail when advisors disabled |

## Next Steps

1. Implement missing audio device endpoints
2. Implement ONNX file upload/download feature
3. Add proper error handling in frontend for missing endpoints
4. Add fallback/mock data in frontend when endpoints unavailable
