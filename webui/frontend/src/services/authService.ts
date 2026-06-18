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
