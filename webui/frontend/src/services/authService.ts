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
        } else {
          throw new Error("Failed to get user info");
        }
      } catch (e: any) {
        if (e.message === "Failed to get user info") throw e;
        // Other fetch errors continue to no-auth check
      }
    }

    // Check for no-auth mode by hitting the config endpoint
    try {
      const configUrl = `${this.baseUrl}/config`;
      const confRes = await fetch(configUrl);
      if (confRes.ok) {
        // No-auth mode detected
        return { username: 'local_admin', roles: ['admin'], is_active: true, noAuth: true };
      }
    } catch (e) {
      // Failed to check no-auth mode
    }

    if (!token) {
      throw new Error("No token available");
    }

    throw new Error("Authentication required");
  }

  logout(): void {
    localStorage.removeItem("auth_token");
  }
}

export const authService = new AuthService();
