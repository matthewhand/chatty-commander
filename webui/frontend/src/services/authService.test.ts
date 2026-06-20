import { vi } from "vitest";
import {
  authService,
  authedFetch,
  subscribeSessionExpired,
  notifySessionExpired,
  resetSessionExpiry,
  hasStoredToken,
} from "./authService";

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

describe("session-expiry / authedFetch", () => {
  beforeEach(() => {
    localStorage.clear();
    mockFetch.mockClear();
    getItemSpy.mockClear();
    removeItemSpy.mockClear();
    // Re-arm the once-per-expiry latch between tests.
    resetSessionExpiry();
  });

  test("hasStoredToken reflects token presence", () => {
    expect(hasStoredToken()).toBe(false);
    localStorage.setItem("auth_token", "t");
    expect(hasStoredToken()).toBe(true);
  });

  test("authedFetch attaches the bearer token when present", async () => {
    localStorage.setItem("auth_token", "abc");
    mockFetch.mockResolvedValueOnce({ ok: true, status: 200 } as Response);

    await authedFetch("/api/v1/anything");

    const init = mockFetch.mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer abc");
  });

  test("a 401 with a token clears the token and notifies subscribers", async () => {
    localStorage.setItem("auth_token", "abc");
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 } as Response);

    const res = await authedFetch("/api/v1/protected");

    expect(res.status).toBe(401);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith(
      "Your session expired — please sign in again",
    );
    // Token was cleared as part of the expiry flow.
    expect(localStorage.getItem("auth_token")).toBeNull();

    unsubscribe();
  });

  test("a 401 with NO token does not trigger expiry (no-auth/dev flow intact)", async () => {
    // No token stored — a 401 here is the normal "please sign in" path.
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 } as Response);

    const res = await authedFetch("/api/v1/protected");

    expect(res.status).toBe(401);
    expect(listener).not.toHaveBeenCalled();

    unsubscribe();
  });

  test("a non-401 error with a token does not trigger expiry", async () => {
    localStorage.setItem("auth_token", "abc");
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 } as Response);

    await authedFetch("/api/v1/protected");

    expect(listener).not.toHaveBeenCalled();
    expect(localStorage.getItem("auth_token")).toBe("abc");

    unsubscribe();
  });

  test("notifySessionExpired fires listeners only once until reset", () => {
    localStorage.setItem("auth_token", "abc");
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    notifySessionExpired();
    notifySessionExpired(); // latched — should not double-fire
    expect(listener).toHaveBeenCalledTimes(1);

    // After a fresh token + reset, a later expiry fires again.
    localStorage.setItem("auth_token", "def");
    resetSessionExpiry();
    notifySessionExpired();
    expect(listener).toHaveBeenCalledTimes(2);

    unsubscribe();
  });

  test("notifySessionExpired no-ops when there is no token", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    notifySessionExpired();

    expect(listener).not.toHaveBeenCalled();
    unsubscribe();
  });

  test("login re-arms the expiry latch on success", async () => {
    localStorage.setItem("auth_token", "abc");
    const listener = vi.fn();
    const unsubscribe = subscribeSessionExpired(listener);

    // First expiry fires once and latches.
    notifySessionExpired();
    expect(listener).toHaveBeenCalledTimes(1);

    // A successful login resets the latch.
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ access_token: "t", token_type: "bearer", expires_in: 1 }),
    } as Response);
    await authService.login("user", "pass");

    localStorage.setItem("auth_token", "t");
    notifySessionExpired();
    expect(listener).toHaveBeenCalledTimes(2);

    unsubscribe();
  });
});
