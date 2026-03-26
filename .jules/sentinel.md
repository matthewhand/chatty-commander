## 2024-05-30 - Fix Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware was using `path.startswith("/api/")` to protect endpoints and checking `path.startswith()` for public endpoints, but it did not normalize paths, allowing a path traversal bypass like `/docs/../api/secret`. Additionally, it allowed partial matches like `/docs-bypassed` to pass as public endpoints.
**Learning:** ASGI applications (like FastAPI/Starlette) do not always pre-normalize `request.url.path` before custom middleware is called. The `.startswith()` string method is insecure for checking URL paths because it does not understand directory boundaries and doesn't handle `..` components.
**Prevention:** Always normalize incoming HTTP paths using `posixpath.normpath(request.url.path)` before access control checks. Always use exact path matching (`path == endpoint`) or strict directory boundary checks (`path.startswith(endpoint + "/")`) when verifying route access.

## 2024-06-19 - Fix Mass Assignment in Config API Endpoint
**Vulnerability:** The `PUT /api/v1/config` endpoint allowed arbitrary key-value pairs to be injected into the application's configuration without validation.
**Learning:** The configuration update method (`cfg.update(config_data)`) did not restrict which keys could be modified, allowing an attacker to overwrite critical settings like `commands`, `web_server`, or execution endpoints by simply including them in the JSON payload.
**Prevention:** Always implement an explicit allowlist (e.g., `ALLOWED_CONFIG_KEYS`) for configuration fields exposed to API modification. Filter incoming payloads against this allowlist before applying state updates.
