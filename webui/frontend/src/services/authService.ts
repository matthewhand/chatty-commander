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

    // Attempt normal token auth if token exists
    if (token) {
      const response = await fetch(`${this.baseUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        return response.json();
      }
    }

    // If we're here, we either had no token or the token was invalid.
    // Let's check if the backend is actually running in --no-auth mode
    // We can test this by trying to load the config endpoint without a token.
    try {
      const confRes = await fetch(`${this.baseUrl}/config`);
      if (confRes.ok) {
        // We successfully fetched config without auth! The server is in no-auth mode.
        return { username: 'local_admin', roles: ['admin'], is_active: true, noAuth: true };
      }
    } catch {
      // Ignore connection errors
    }

    throw new Error("Authentication required");
  }

  logout(): void {
    localStorage.removeItem("auth_token");
  }
}

export const authService = new AuthService();
