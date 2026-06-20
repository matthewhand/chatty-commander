import { vi } from "vitest";

// Spy on the shared session-expiry path so we can assert apiService routes its
// authenticated 401s through it. The rest of authService keeps its real impl.
vi.mock("./authService", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, notifySessionExpired: vi.fn() };
});

import apiService from "./apiService";
import { notifySessionExpired } from "./authService";

beforeAll(() => {
  global.fetch = vi.fn();
  apiService.setBaseURL("http://localhost:8100");
});

describe("ApiService", () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test("makes GET requests successfully", async () => {
    const mockData = { status: "success" };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      text: () => Promise.resolve(JSON.stringify(mockData)),
      headers: { get: () => "application/json" },
    });

    const result = await apiService.get("/test");

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/test",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    expect(result).toEqual(mockData);
  });

  test("makes POST requests with data", async () => {
    const mockResponse = { id: 1, created: true };
    const postData = { name: "test" };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
      text: () => Promise.resolve(JSON.stringify(mockResponse)),
      headers: { get: () => "application/json" },
    });

    const result = await apiService.post("/create", postData);

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/create",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
        body: JSON.stringify(postData),
      }),
    );
    expect(result).toEqual(mockResponse);
  });

  test("handles API errors", async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(""),
      headers: { get: () => "application/json" },
    });

    await expect(apiService.get("/error")).rejects.toThrow(/HTTP 500/);
  });

  test("handles network errors", async () => {
    fetch.mockRejectedValueOnce(new Error("Network error"));

    await expect(apiService.get("/network-error")).rejects.toThrow(
      "Network error",
    );
  });

  test("includes authorization header when token is present", async () => {
    localStorage.setItem("auth_token", "test-token");

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(JSON.stringify({})),
      headers: { get: () => "application/json" },
    });

    await apiService.get("/protected");

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/protected",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      }),
    );
    localStorage.removeItem("auth_token");
  });

  test("a 401 with a token triggers the shared session-expiry path", async () => {
    localStorage.setItem("auth_token", "test-token");
    notifySessionExpired.mockClear();

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(""),
      headers: { get: () => "application/json" },
    });

    await expect(apiService.getStatus()).rejects.toThrow(/HTTP 401/);
    expect(notifySessionExpired).toHaveBeenCalledTimes(1);

    localStorage.removeItem("auth_token");
  });

  test("a 401 without a token does NOT trigger the session-expiry path", async () => {
    localStorage.removeItem("auth_token");
    notifySessionExpired.mockClear();

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(""),
      headers: { get: () => "application/json" },
    });

    await expect(apiService.getStatus()).rejects.toThrow(/HTTP 401/);
    expect(notifySessionExpired).not.toHaveBeenCalled();
  });

  test("health check endpoint", async () => {
    const healthData = { status: "healthy", uptime: 12345 };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(healthData),
      text: () => Promise.resolve(JSON.stringify(healthData)),
      headers: { get: () => "application/json" },
    });

    const result = await apiService.healthCheck();

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/health",
      expect.any(Object),
    );
    expect(result).toEqual(healthData);
  });
});
