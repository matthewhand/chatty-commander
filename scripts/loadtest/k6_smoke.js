/**
 * k6 smoke / baseline load test for the ChattyCommander web API.
 *
 * Exercises the read-only API surface registered in
 * src/chatty_commander/web/routes/ (core.py, audio.py, themes.py):
 *
 *   GET /health               (core.py)   - liveness probe
 *   GET /api/v1/status        (core.py)   - system status
 *   GET /api/v1/config        (core.py)   - sanitized config
 *   GET /api/v1/state         (core.py)   - current state machine state
 *   GET /api/audio/devices    (audio.py)  - audio device enumeration
 *   GET /api/themes           (themes.py) - available avatar/UI themes
 *
 * Usage:
 *   k6 run -e BASE_URL=http://localhost:8100 scripts/loadtest/k6_smoke.js
 *   k6 run -e BASE_URL=https://host:8100 -e API_KEY=secret scripts/loadtest/k6_smoke.js
 *
 * Env vars:
 *   BASE_URL - server root (default http://localhost:8100)
 *   API_KEY  - optional; sent as the X-API-Key header. Omit when the server
 *              runs with --no-auth.
 *
 * Thresholds (the performance baseline this repo commits to):
 *   - p95 < 200ms for the hot paths /health and /api/v1/status
 *   - p95 < 500ms for the remaining endpoints
 *   - overall HTTP error rate < 1%
 */
import http from 'k6/http';
import { check, group } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8100';
const API_KEY = __ENV.API_KEY || '';

const params = {
  headers: Object.assign(
    { Accept: 'application/json' },
    API_KEY ? { 'X-API-Key': API_KEY } : {}
  ),
};

export const options = {
  // Staged ramp: warm up, hold ~20 VUs, ramp down.
  // Override with --vus/--duration for a quick smoke run.
  stages: [
    { duration: '30s', target: 5 },
    { duration: '30s', target: 20 },
    { duration: '60s', target: 20 },
    { duration: '15s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'], // error rate < 1%
    // Hot paths: health/status must answer fast.
    'http_req_duration{endpoint:health}': ['p(95)<200'],
    'http_req_duration{endpoint:status}': ['p(95)<200'],
    // Everything else: p95 < 500ms.
    'http_req_duration{endpoint:config}': ['p(95)<500'],
    'http_req_duration{endpoint:state}': ['p(95)<500'],
    'http_req_duration{endpoint:audio_devices}': ['p(95)<500'],
    'http_req_duration{endpoint:themes}': ['p(95)<500'],
  },
};

function get(path, endpointTag) {
  const res = http.get(`${BASE_URL}${path}`, {
    headers: params.headers,
    tags: { endpoint: endpointTag },
  });
  check(
    res,
    {
      [`${path} status is 200`]: (r) => r.status === 200,
      [`${path} returns JSON`]: (r) =>
        (r.headers['Content-Type'] || '').includes('application/json'),
    },
    { endpoint: endpointTag }
  );
  return res;
}

export default function () {
  group('hot paths', () => {
    get('/health', 'health');
    get('/api/v1/status', 'status');
  });

  group('core api', () => {
    get('/api/v1/config', 'config');
    get('/api/v1/state', 'state');
  });

  group('peripherals', () => {
    get('/api/audio/devices', 'audio_devices');
    get('/api/themes', 'themes');
  });
}
