import { vi } from "vitest";
import { authService } from "./authService";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

// Spy on jsdom's real localStorage so tests can control token presence.
const getItemSpy = vi.spyOn(Storage.prototype, "getItem");
const removeItemSpy = vi.spyOn(Storage.prototype, "removeItem");

describe("AuthService", () => {
  beforeEach(() => {
    localStorage.clear();
    mockFetch.mockClear();
    getItemSpy.mockClear();
    removeItemSpy.mockClear();
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

    expect(removeItemSpy).toHaveBeenCalledWith("auth_token");
    expect(localStorage.getItem("auth_token")).toBeNull();
  });

  test("getCurrentUser returns user data when token exists", async () => {
    const userData = { username: "testuser", is_active: true, roles: ["user"] };
    // Ensure token exists before calling
    getItemSpy.mockReturnValueOnce("valid-token");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(userData),
    } as Response);

    const user = await authService.getCurrentUser();

    expect(user).toEqual(userData);
  });

  test("getCurrentUser throws when no token and no-auth probe fails", async () => {
    // No token, and the /config probe is unreachable -> auth is required.
    getItemSpy.mockReturnValueOnce(null);
    mockFetch.mockRejectedValueOnce(new Error("network"));

    await expect(authService.getCurrentUser()).rejects.toThrow(
      "Authentication required",
    );
  });

  test("getCurrentUser grants no-auth session when config endpoint is reachable", async () => {
    // No token, but /config responds OK -> backend has auth disabled.
    getItemSpy.mockReturnValueOnce(null);
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

  test("classifies a 401 as a credentials failure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    } as Response);

    await expect(authService.login("wrong", "creds")).rejects.toMatchObject({
      kind: "credentials",
    });
    expect(authService.lastLoginErrorKind).toBe("credentials");
  });

  test("classifies a 5xx as a network/reachability failure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
    } as Response);

    await expect(authService.login("user", "pass")).rejects.toMatchObject({
      kind: "network",
    });
    expect(authService.lastLoginErrorKind).toBe("network");
  });

  test("classifies a fetch rejection as a network failure", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Failed to fetch"));

    await expect(authService.login("user", "pass")).rejects.toMatchObject({
      kind: "network",
    });
    expect(authService.lastLoginErrorKind).toBe("network");
  });

  test("clears the last error kind on a successful login", async () => {
    authService.lastLoginErrorKind = "credentials";
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: "t", token_type: "bearer", expires_in: 1 }),
    } as Response);

    await authService.login("user", "pass");

    expect(authService.lastLoginErrorKind).toBeNull();
  });

  test("getCurrentUser falls back to no-auth probe when token is rejected", async () => {
    // Token present but rejected (401); the no-auth /config probe then succeeds,
    // so we get a local admin session rather than a hard failure.
    getItemSpy.mockReturnValueOnce("invalid-token");
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
    getItemSpy.mockReturnValueOnce("invalid-token");
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
