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

  test("getCurrentUser throws error when no token", async () => {
    await expect(authService.getCurrentUser()).rejects.toThrow(
      "No token available",
    );
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

  test("getCurrentUser handles API errors", async () => {
    // Ensure token is present so we exercise the fetch error path
    (localStorage.getItem as jest.Mock).mockReturnValueOnce("invalid-token");
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    } as Response);

    await expect(authService.getCurrentUser()).rejects.toThrow(
      "Failed to get user info",
    );
  });
});
