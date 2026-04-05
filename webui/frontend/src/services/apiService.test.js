import { vi, describe, test, expect, beforeAll, beforeEach } from "vitest";
import apiService from "./apiService";

beforeAll(() => {
  global.fetch = vi.fn();
  apiService.setBaseURL("http://localhost:8100");

  // Provide a minimal localStorage mock (forcing it to ensure it's used)
  const mockLocalStorage = {
    store: {},
    getItem: vi.fn((k) => mockLocalStorage.store[k] ?? null),
    setItem: vi.fn((k, v) => {
      mockLocalStorage.store[k] = v;
    }),
    removeItem: vi.fn((k) => {
      delete mockLocalStorage.store[k];
    }),
    clear: vi.fn(() => {
      mockLocalStorage.store = {};
    }),
  };

  Object.defineProperty(global, "localStorage", {
    value: mockLocalStorage,
    writable: true,
    configurable: true,
  });
});

describe("ApiService", () => {
  beforeEach(() => {
    fetch.mockClear();
    if (global.localStorage.clear) {
      global.localStorage.clear();
    }
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
