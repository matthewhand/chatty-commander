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

class AuthService {
  private baseUrl = "/api/v1";

  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

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
        console.warn(
          `authService: token auth rejected (${response.status} ${response.statusText})`,
        );
      } catch (e) {
        console.warn("Auth check failed with token", e);
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
      console.debug("authService: no-auth probe failed", e);
    }

    throw new Error("Authentication required");
  }

  logout(): void {
    localStorage.removeItem("auth_token");
  }
}

export const authService = new AuthService();
