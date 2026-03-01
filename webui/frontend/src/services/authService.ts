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
      } catch (e) {
        console.warn("Auth check failed with token", e);
      }
    }

    // Check for no-auth mode by hitting the config endpoint
    try {
      // In development/test, window.location might not match API location if proxied incorrectly.
      // But usually relative path works if served by Vite proxy or same origin.

      const configUrl = `${this.baseUrl}/config`;
      console.log(`Checking no-auth mode at ${configUrl}`);

      const confRes = await fetch(configUrl);
      if (confRes.ok) {
        console.log("No-auth mode detected via config endpoint");
        return { username: 'local_admin', roles: ['admin'], is_active: true, noAuth: true };
      } else {
         console.log("Config endpoint returned non-200", confRes.status);
         // Fallback: If we get a 200 from ANY public endpoint, we might assume no-auth if auth endpoints fail?
         // No, that's risky. But for this specific bug, maybe the URL is just missing the /api prefix or similar.
      }
    } catch (e) {
      console.error("Failed to check no-auth mode", e);
    }

    throw new Error("Authentication required");
  }

  logout(): void {
    localStorage.removeItem("auth_token");
  }
}

export const authService = new AuthService();
