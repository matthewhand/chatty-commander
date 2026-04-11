## 2024-05-30 - Fix Path Traversal Authentication Bypass
**Vulnerability:** The authentication middleware was using `path.startswith("/api/")` to protect endpoints and checking `path.startswith()` for public endpoints, but it did not normalize paths, allowing a path traversal bypass like `/docs/../api/secret`. Additionally, it allowed partial matches like `/docs-bypassed` to pass as public endpoints.
**Learning:** ASGI applications (like FastAPI/Starlette) do not always pre-normalize `request.url.path` before custom middleware is called. The `.startswith()` string method is insecure for checking URL paths because it does not understand directory boundaries and doesn't handle `..` components.
**Prevention:** Always normalize incoming HTTP paths using `posixpath.normpath(request.url.path)` before access control checks. Always use exact path matching (`path == endpoint`) or strict directory boundary checks (`path.startswith(endpoint + "/")`) when verifying route access.

## 2024-05-24 - [CRITICAL] Fix mass assignment vulnerability in config endpoint
**Vulnerability:** Mass assignment vulnerability in `/api/v1/config` `PUT` endpoint due to lack of allowlist. Any configuration item could be updated by a malicious user.
**Learning:** The core issue is that user input in the `config_data` JSON payload was passed without filtering directly into the application's configuration `cfg.update(config_data)`.
**Prevention:** Use an explicit allowlist (like `ALLOWED_CONFIG_KEYS`) to filter user-supplied configuration payloads before updating the underlying configuration store. This enforces strict boundaries on what can be changed via the API.

## 2024-05-30 - Authorization Bypass via Missing API Key Configuration
**Vulnerability:** The application's `AuthMiddleware` contained a fail-open condition where, if the `api_key` configuration property was completely missing or empty, it allowed unauthenticated requests to pass through to protected endpoints. This bypassed intended security completely.
**Learning:** Security mechanisms often attempt to handle empty configurations gracefully, but doing so without enforcing a secure default (`no_auth=True` or returning an error) leads to unintentional fail-open behavior. Authentication logic should never bypass the actual validation step unless explicitly operating in an insecure mode.
**Prevention:** Always default to denying access (returning a 401 Unauthorized or similar) if a required security credential configuration is missing. Ensure that the core credential comparison function gracefully handles `None` or empty strings to return `False`, avoiding the need for complex, potentially unsafe manual bypasses.

## 2024-06-25 - [CRITICAL] Web mode API routes bypass AuthMiddleware when trailing slashes are absent
**Vulnerability:** The web server included routes globally via `app.include_router()` and was missing the `AuthMiddleware` entirely in `WebModeServer._create_app()`, which means `no_auth` setting or `api_key` verification wasn't effectively globally applied through the middleware across `/api` endpoints.
**Learning:** Registration of `AuthMiddleware` in `WebModeServer._create_app` is required to enforce API key protection globally across all `/api` endpoints in the production application.
**Prevention:** Ensure the `AuthMiddleware` is added to the application middleware stack alongside other security middlewares (e.g. `SecurityHeadersMiddleware`).
