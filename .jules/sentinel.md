## 2024-05-30 - Fix Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware was using `path.startswith("/api/")` to protect endpoints and checking `path.startswith()` for public endpoints, but it did not normalize paths, allowing a path traversal bypass like `/docs/../api/secret`. Additionally, it allowed partial matches like `/docs-bypassed` to pass as public endpoints.
**Learning:** ASGI applications (like FastAPI/Starlette) do not always pre-normalize `request.url.path` before custom middleware is called. The `.startswith()` string method is insecure for checking URL paths because it does not understand directory boundaries and doesn't handle `..` components.
**Prevention:** Always normalize incoming HTTP paths using `posixpath.normpath(request.url.path)` before access control checks. Always use exact path matching (`path == endpoint`) or strict directory boundary checks (`path.startswith(endpoint + "/")`) when verifying route access.
## 2026-03-21 - [Mass Assignment in Config PUT Endpoint]
**Vulnerability:** The `/api/v1/config` PUT endpoint allowed updating any configuration key by passing an arbitrary JSON payload.
**Learning:** This allowed an attacker to overwrite sensitive or internal configuration values, inject unexpected variables, or disrupt the application (e.g., modifying `commands` or `api_endpoints`).
**Prevention:** Implement strict allowlists (`ALLOWED_CONFIG_KEYS`) to filter and validate input payloads before updating sensitive configuration objects, adhering to the Principle of Least Privilege.
