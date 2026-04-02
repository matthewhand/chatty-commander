## 2024-05-30 - Fix Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware was using `path.startswith("/api/")` to protect endpoints and checking `path.startswith()` for public endpoints, but it did not normalize paths, allowing a path traversal bypass like `/docs/../api/secret`. Additionally, it allowed partial matches like `/docs-bypassed` to pass as public endpoints.
**Learning:** ASGI applications (like FastAPI/Starlette) do not always pre-normalize `request.url.path` before custom middleware is called. The `.startswith()` string method is insecure for checking URL paths because it does not understand directory boundaries and doesn't handle `..` components.
**Prevention:** Always normalize incoming HTTP paths using `posixpath.normpath(request.url.path)` before access control checks. Always use exact path matching (`path == endpoint`) or strict directory boundary checks (`path.startswith(endpoint + "/")`) when verifying route access.

## 2024-05-24 - [CRITICAL] Fix mass assignment vulnerability in config endpoint
**Vulnerability:** Mass assignment vulnerability in `/api/v1/config` `PUT` endpoint due to lack of allowlist. Any configuration item could be updated by a malicious user.
**Learning:** The core issue is that user input in the `config_data` JSON payload was passed without filtering directly into the application's configuration `cfg.update(config_data)`.
**Prevention:** Use an explicit allowlist (like `ALLOWED_CONFIG_KEYS`) to filter user-supplied configuration payloads before updating the underlying configuration store. This enforces strict boundaries on what can be changed via the API.
## 2024-04-02 - URL-Encoded Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware used `request.url.path` directly with `posixpath.normpath` without manual URL decoding. This allowed attackers to bypass authentication by URL-encoding or double-encoding path traversal sequences (e.g., `/docs%2f..%2fapi/secret`), which the middleware treated as a public `/docs` subpath, but the underlying framework routed to the protected `/api` endpoint.
**Learning:** In ASGI applications like FastAPI and Starlette, `request.url.path` retains the raw URL-encoded path. Middleware that enforces security policies based on paths must manually unquote the path to match the final routing resolution.
**Prevention:** Implement a bounded loop of `urllib.parse.unquote` before applying `posixpath.normpath` in middleware to ensure all layers of URL encoding are resolved prior to security checks.
