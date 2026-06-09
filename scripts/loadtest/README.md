# Load testing / performance baselines

k6 scripts for establishing and tracking latency baselines of the
ChattyCommander web API (ROADMAP P2 "Production hardening").

Contents:

- `k6_smoke.js` — staged-load test of the read-only API surface
  (`/health`, `/api/v1/status`, `/api/v1/config`, `/api/v1/state`,
  `/api/audio/devices`, `/api/themes`).

## 1. Start the server under test

On a dedicated test box (never against production), run the web server
without auth:

```bash
uv run chatty-commander --web --no-auth --port 8100
```

`--no-auth` is fine for an isolated load-test host. If you instead test an
auth-enabled deployment, pass the key via `API_KEY` (sent as the
`X-API-Key` header).

## 2. Run k6

### With Docker (no local install)

```bash
docker run --rm --network=host \
  -v "$(pwd)/scripts/loadtest:/scripts:ro" \
  grafana/k6 run -e BASE_URL=http://localhost:8100 /scripts/k6_smoke.js
```

`--network=host` lets the container reach a server on the host (Linux).
On macOS/Windows use `-e BASE_URL=http://host.docker.internal:8100` and
drop `--network=host`.

### With a local k6 binary

```bash
k6 run -e BASE_URL=http://localhost:8100 scripts/loadtest/k6_smoke.js
```

### Against an auth-enabled server

```bash
k6 run -e BASE_URL=https://test-host:8100 -e API_KEY=yourkey scripts/loadtest/k6_smoke.js
```

### Quick smoke (10 seconds, 2 VUs)

CLI flags override the staged profile in the script:

```bash
k6 run -e BASE_URL=http://localhost:8100 --duration 10s --vus 2 scripts/loadtest/k6_smoke.js
```

## Load profile

The default profile in `k6_smoke.js` ramps 0 → 5 VUs (30s), 5 → 20 VUs
(30s), holds 20 VUs (60s), then ramps down (15s). Each VU iteration hits
all six endpoints sequentially.

## Thresholds (what pass/fail means)

| Metric | Target | Rationale |
|---|---|---|
| `http_req_duration{endpoint:health}` p95 | < 200 ms | Liveness probe; load balancers/orchestrators poll it and time out fast. |
| `http_req_duration{endpoint:status}` p95 | < 200 ms | Hot path polled by the UI; must stay snappy under load. |
| `http_req_duration{endpoint:config}` p95 | < 500 ms | Heavier serialization; read at page load, not polled. |
| `http_req_duration{endpoint:state}` p95 | < 500 ms | State-machine snapshot. |
| `http_req_duration{endpoint:audio_devices}` p95 | < 500 ms | May enumerate hardware. |
| `http_req_duration{endpoint:themes}` p95 | < 500 ms | Static-ish theme list. |
| `http_req_failed` rate | < 1% | Any sustained error rate under read-only load is a regression. |

k6 exits non-zero if any threshold fails, so the script can gate CI or a
release checklist. p95 (not average) is used because tail latency is what
users feel; averages hide stalls.

## Recording baselines

After each meaningful change (release, dependency bump, infra move), run
the full staged profile and append a row per endpoint. Always note the
hardware/environment — numbers are only comparable within an environment.

### Results table template

| Date | Commit | Environment | Profile | Endpoint | p95 (ms) | avg (ms) | max (ms) | Err rate | req/s (total) | Pass? |
|---|---|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | abcdef1 | (cpu/ram/os, server flags) | staged 20 VU / 2m15s | /health | | | | | | |

### Measured baselines

| Date | Commit | Environment | Profile | Endpoint | p95 (ms) | avg (ms) | max (ms) | Err rate | req/s (total) | Pass? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /health | 3.56 | 2.60 | 4.54 | 0.00% | 707.9 | yes |
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /api/v1/status | 3.71 | 2.71 | 108.56 | 0.00% | 707.9 | yes |
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /api/v1/config | 4.03 | 3.13 | 108.53 | 0.00% | 707.9 | yes |
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /api/v1/state | 3.73 | 2.64 | 5.07 | 0.00% | 707.9 | yes |
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /api/audio/devices | 3.51 | 2.69 | 110.03 | 0.00% | 707.9 | yes |
| 2026-06-10 | cc52b876 | Linux 6.8 dev box, localhost, `--web --no-auth --port 8100` | smoke 2 VU / 10s | /api/themes | 3.50 | 2.63 | 109.67 | 0.00% | 707.9 | yes |

Notes on the 2026-06-10 smoke run: 7,128 requests, 14,256 checks, 100%
passed; all thresholds green. The ~110 ms max outliers appear to be a
one-off warm-up stall, not steady-state behavior. This was a quick smoke
(2 VUs / 10s via Docker `grafana/k6`, `--network=host`), not the full
staged 20 VU profile — re-run the staged profile on representative
hardware before treating these as release baselines.
