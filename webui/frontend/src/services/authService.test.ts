import { authService } from "./authService";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch as any;

// Mock localStorage methods
beforeAll(() => {
  Object.defineProperty(global, "localStorage", {
    value: {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  });
});

describe("AuthService", () => {
  beforeEach(() => {
    localStorage.clear();
    mockFetch.mockClear();
    (localStorage.getItem as jest.Mock).mockClear();
    (localStorage.setItem as jest.Mock).mockClear();
    (localStorage.removeItem as jest.Mock).mockClear();
  });

  test("login returns token response", async () => {
    const mockResponse = {
      access_token: "test-token",
      token_type: "bearer",
      expires_in: 3600,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    } as Response);

    const result = await authService.login("testuser", "password");

    expect(result).toEqual(mockResponse);
  });

  test("logout removes token from storage", () => {
    localStorage.setItem("auth_token", "test-token");

    authService.logout();

    expect(localStorage.removeItem).toHaveBeenCalledWith("auth_token");
  });

  test("getCurrentUser returns user data when token exists", async () => {
    const userData = { username: "testuser", is_active: true, roles: ["user"] };
    // Ensure token exists before calling
    (localStorage.getItem as jest.Mock).mockReturnValueOnce("valid-token");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(userData),
    } as Response);

    const user = await authService.getCurrentUser();

    expect(user).toEqual(userData);
  });

  test("getCurrentUser throws when no token and no-auth probe fails", async () => {
    // No token, and the /config probe is unreachable -> auth is required.
    (localStorage.getItem as jest.Mock).mockReturnValueOnce(null);
    mockFetch.mockRejectedValueOnce(new Error("network"));

    await expect(authService.getCurrentUser()).rejects.toThrow(
      "Authentication required",
    );
  });

  test("getCurrentUser grants no-auth session when config endpoint is reachable", async () => {
    // No token, but /config responds OK -> backend has auth disabled.
    (localStorage.getItem as jest.Mock).mockReturnValueOnce(null);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    } as Response);

    const user = await authService.getCurrentUser();

    expect(user.noAuth).toBe(true);
    expect(user.roles).toContain("admin");
  });

  test("handles login errors", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    } as Response);

    await expect(authService.login("wrong", "credentials")).rejects.toThrow(
      "Login failed",
    );
  });

  test("getCurrentUser falls back to no-auth probe when token is rejected", async () => {
    // Token present but rejected (401); the no-auth /config probe then succeeds,
    // so we get a local admin session rather than a hard failure.
    (localStorage.getItem as jest.Mock).mockReturnValueOnce("invalid-token");
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);

    const user = await authService.getCurrentUser();

    expect(user.noAuth).toBe(true);
  });

  test("getCurrentUser throws when token rejected and no-auth probe also fails", async () => {
    (localStorage.getItem as jest.Mock).mockReturnValueOnce("invalid-token");
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      } as Response)
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      } as Response);

    await expect(authService.getCurrentUser()).rejects.toThrow(
      "Authentication required",
    );
  });
});
