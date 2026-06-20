import { logger } from "../utils/logger";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  username: string;
  is_active: boolean;
  roles: string[];
  noAuth?: boolean;
}

/**
 * Why a login failed, so the UI can show actionable copy instead of one
 * generic message:
 *  - "credentials": the server answered and rejected the username/password (401)
 *  - "network": the server couldn't be reached, or returned a server-side
 *    error (5xx / fetch threw) — retrying may help once it's back.
 */
export type LoginErrorKind = "credentials" | "network";

/**
 * User-facing copy shown when a previously-authenticated session is rejected
 * mid-session (the backend returned 401 for a request that carried a token, or
 * a WebSocket was closed with an auth-policy code). Centralised here so the
 * REST and WebSocket paths surface identical wording.
 */
export const SESSION_EXPIRED_MESSAGE =
  "Your session expired — please sign in again";

type SessionExpiredListener = (message: string) => void;

/**
 * Module-level pub/sub for "the session just expired" events.
 *
 * This lives at module scope (not inside React) on purpose: the 401 can be
 * detected deep in the fetch layer (`api.ts`) or in `WebSocketProvider`, both
 * of which sit at a different point in the provider tree than `useAuth`. A
 * plain event bus lets any of them signal expiry without prop-drilling or
 * coupling to React context ordering.
 */
const sessionExpiredListeners = new Set<SessionExpiredListener>();

/**
 * Subscribe to session-expiry events. Returns an unsubscribe function.
 */
export function subscribeSessionExpired(
  listener: SessionExpiredListener,
): () => void {
  sessionExpiredListeners.add(listener);
  return () => {
    sessionExpiredListeners.delete(listener);
  };
}

/**
 * Whether a bearer token is currently stored. Used to decide whether a 401 is
 * an *expiry* of an existing session (token present) versus the normal
 * unauthenticated / no-auth flow (no token), which must keep behaving as today.
 */
export function hasStoredToken(): boolean {
  try {
    return Boolean(localStorage.getItem("auth_token"));
  } catch {
    return false;
  }
}

let sessionExpiryInFlight = false;

/**
 * Signal that the current session has expired: clear the stored token and
 * notify subscribers exactly once per expiry. Idempotent across the burst of
 * parallel 401s a page often produces — listeners fire a single time until the
 * next successful (re)authentication resets the latch via {@link resetSessionExpiry}.
 *
 * No-ops when there is no stored token, so the dev/no-auth flow (which never
 * stores a token) is never disturbed.
 */
export function notifySessionExpired(
  message: string = SESSION_EXPIRED_MESSAGE,
): void {
  if (!hasStoredToken()) return;
  if (sessionExpiryInFlight) return;
  sessionExpiryInFlight = true;

  try {
    localStorage.removeItem("auth_token");
  } catch {
    /* storage unavailable — listeners still need to fire */
  }

  for (const listener of sessionExpiredListeners) {
    try {
      listener(message);
    } catch {
      /* a misbehaving listener must not block the others */
    }
  }
}

/**
 * Re-arm the session-expiry latch after a fresh login, so a later expiry is
 * delivered again.
 */
export function resetSessionExpiry(): void {
  sessionExpiryInFlight = false;
}

/**
 * `fetch` wrapper for our own (`/api/v1/...`) backend that:
 *  - attaches the stored bearer token when present;
 *  - centralises 401 handling: a 401 on a request that carried a token means
 *    the session expired/was revoked mid-session, so we trigger the shared
 *    {@link notifySessionExpired} path. A 401 with no token is left untouched
 *    (callers handle it as today; the no-auth flow is unaffected).
 *
 * Returns the raw {@link Response} so existing callers keep full control over
 * status/body handling.
 */
export async function authedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  let token: string | null = null;
  try {
    token = localStorage.getItem("auth_token");
  } catch {
    token = null;
  }

  const headers = new Headers(init.headers ?? {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(input, { ...init, headers });

  // Only an authenticated request (token present) hitting a 401 indicates an
  // expired/invalid session. Without a token, 401 is the expected "please log
  // in" signal and must not nuke state or redirect.
  if (response.status === 401 && token) {
    notifySessionExpired();
  }

  return response;
}

/**
 * Error thrown by {@link AuthService.login}. Keeps the historical
 * message ("Login failed") that callers/tests rely on, while exposing a
 * machine-readable {@link LoginError.kind} for the UI to branch on.
 */
export class LoginError extends Error {
  readonly kind: LoginErrorKind;

  constructor(kind: LoginErrorKind) {
    super("Login failed");
    this.name = "LoginError";
    this.kind = kind;
  }
}

class AuthService {
  private baseUrl = "/api/v1";

  /**
   * The kind of the most recent login failure, or null if the last login
   * succeeded / none has run. This lets a caller that only receives a boolean
   * (e.g. the `useAuth` hook, which swallows the thrown error) still recover
   * *why* the login failed without us changing that hook's contract.
   */
  lastLoginErrorKind: LoginErrorKind | null = null;

  async login(username: string, password: string): Promise<TokenResponse> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });
    } catch {
      // fetch rejects on network failure / DNS / CORS / offline.
      this.lastLoginErrorKind = "network";
      throw new LoginError("network");
    }

    if (!response.ok) {
      // A 401 means the server reached a verdict: bad credentials. Anything
      // else (5xx, 502/503/504 from a proxy, etc.) is a reachability/server
      // problem the user can't fix by re-typing their password.
      const kind: LoginErrorKind =
        response.status === 401 ? "credentials" : "network";
      this.lastLoginErrorKind = kind;
      throw new LoginError(kind);
    }

    this.lastLoginErrorKind = null;
    // A fresh, valid session — re-arm the session-expiry latch so a future
    // expiry of *this* session is delivered to subscribers.
    resetSessionExpiry();
    return response.json();
  }

  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem("auth_token");

    if (token) {
      try {
        const response = await fetch(`${this.baseUrl}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          return await response.json();
        }
        // The token was present but rejected by the backend. Log the reason so
        // an invalid/expired token isn't silently masked by the no-auth probe.
        logger.warn(
          `authService: token auth rejected (${response.status} ${response.statusText})`,
        );
      } catch (e) {
        logger.warn("Auth check failed with token", e);
      }
    }

    // Check for no-auth mode: if the config endpoint is reachable without a
    // token, the backend is running with auth disabled and we grant a local
    // admin session. A relative path works when same-origin or behind the proxy.
    try {
      const confRes = await fetch(`${this.baseUrl}/config`);
      if (confRes.ok) {
        return { username: 'local_admin', roles: ['admin'], is_active: true, noAuth: true };
      }
    } catch (e) {
      logger.debug("authService: no-auth probe failed", e);
    }

    throw new Error("Authentication required");
  }

  logout(): void {
    localStorage.removeItem("auth_token");
  }
}

export const authService = new AuthService();
