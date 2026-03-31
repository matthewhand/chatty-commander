## 2024-05-30 - Fix Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware was using `path.startswith("/api/")` to protect endpoints and checking `path.startswith()` for public endpoints, but it did not normalize paths, allowing a path traversal bypass like `/docs/../api/secret`. Additionally, it allowed partial matches like `/docs-bypassed` to pass as public endpoints.
**Learning:** ASGI applications (like FastAPI/Starlette) do not always pre-normalize `request.url.path` before custom middleware is called. The `.startswith()` string method is insecure for checking URL paths because it does not understand directory boundaries and doesn't handle `..` components.
**Prevention:** Always normalize incoming HTTP paths using `posixpath.normpath(request.url.path)` before access control checks. Always use exact path matching (`path == endpoint`) or strict directory boundary checks (`path.startswith(endpoint + "/")`) when verifying route access.

## 2024-05-24 - [CRITICAL] Fix mass assignment vulnerability in config endpoint
**Vulnerability:** Mass assignment vulnerability in `/api/v1/config` `PUT` endpoint due to lack of allowlist. Any configuration item could be updated by a malicious user.
**Learning:** The core issue is that user input in the `config_data` JSON payload was passed without filtering directly into the application's configuration `cfg.update(config_data)`.
**Prevention:** Use an explicit allowlist (like `ALLOWED_CONFIG_KEYS`) to filter user-supplied configuration payloads before updating the underlying configuration store. This enforces strict boundaries on what can be changed via the API.

## 2024-06-05 - Fix URL-Encoded Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware used `posixpath.normpath(request.url.path)` to prevent path traversal attacks, but it did not URL-decode the path first. An attacker could bypass the authentication by URL-encoding the path traversal characters (e.g., `/docs%2f..%2fapi/secret`), which bypasses the `normpath` check but is still correctly routed by the underlying framework.
**Learning:** Path normalization functions like `posixpath.normpath` do not automatically decode URL-encoded characters. If the path is not decoded first, encoded directory traversal sequences (`%2f..%2f`) are treated as literal strings and not resolved, leading to bypasses when the underlying routing mechanism eventually decodes them.
**Prevention:** Always URL-decode the path (handling potential multiple encodings) using `urllib.parse.unquote` in a loop until it stops changing *before* applying `posixpath.normpath` for access control checks.
