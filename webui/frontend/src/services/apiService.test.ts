import { vi, describe, test, expect, beforeAll, beforeEach, Mock } from "vitest";
import apiService from "./apiService";

beforeAll(() => {
  global.fetch = vi.fn();
  apiService.setBaseURL("http://localhost:8100");

  // Provide a minimal localStorage mock (forcing it to ensure it's used)
  const mockLocalStorage = {
    store: {} as Record<string, string>,
    getItem: vi.fn((k: string) => mockLocalStorage.store[k] ?? null),
    setItem: vi.fn((k: string, v: string) => {
      mockLocalStorage.store[k] = v;
    }),
    removeItem: vi.fn((k: string) => {
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
    (fetch as Mock).mockClear();
    if (global.localStorage.clear) {
      global.localStorage.clear();
    }
  });

  test("makes GET requests successfully", async () => {
    const mockData = { status: "success" };
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      text: () => Promise.resolve(JSON.stringify(mockData)),
      headers: new Headers({ "content-type": "application/json" }),
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

    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
      text: () => Promise.resolve(JSON.stringify(mockResponse)),
      headers: new Headers({ "content-type": "application/json" }),
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
    (fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(""),
      headers: new Headers({ "content-type": "application/json" }),
    });

    await expect(apiService.get("/error")).rejects.toThrow(/HTTP 500/);
  });

  test("handles network errors", async () => {
    (fetch as Mock).mockRejectedValueOnce(new Error("Network error"));

    await expect(apiService.get("/network-error")).rejects.toThrow(
      "Network error",
    );
  });

  test("includes authorization header when token is present", async () => {
    localStorage.setItem("auth_token", "test-token");

    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(JSON.stringify({})),
      headers: new Headers({ "content-type": "application/json" }),
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
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(healthData),
      text: () => Promise.resolve(JSON.stringify(healthData)),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.healthCheck();

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/health",
      expect.any(Object),
    );
    expect(result).toEqual(healthData);
  });

  test("fetchAgentStatus endpoint", async () => {
    const mockData = { contexts: { "key1": { persona_id: "test", last_updated: "2024-01-01" } } };
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.fetchAgentStatus();
    expect(result).toHaveLength(1);
    expect(result[0].name).toContain("test");
  });

  test("fetchLLMModels endpoint", async () => {
    const mockData = { data: [{ id: "model1" }, "model2"] };
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.fetchLLMModels("http://other-api", "key");
    expect(result).toEqual(["model1", "model2"]);
  });

  test("fetchVoiceModels endpoint", async () => {
    const mockData = { models: [{ name: "voice1" }] };
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.fetchVoiceModels();
    expect(result).toEqual(mockData.models);
  });

  test("uploadVoiceModel uses FormData", async () => {
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const file = new File([""], "test.onnx");
    await apiService.uploadVoiceModel(file, "idle");

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/api/v1/models/upload",
      expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      }),
    );
  });

  test("deleteVoiceModel endpoint", async () => {
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
      headers: new Headers({ "content-type": "application/json" }),
    });

    await apiService.deleteVoiceModel("test.onnx");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/api/v1/models/files/test.onnx",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  test("fetchAgentBlueprints endpoint", async () => {
    const mockData = [{ id: "1", name: "Agent 1" }];
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.fetchAgentBlueprints();
    expect(result).toEqual(mockData);
  });

  test("createAgentBlueprint endpoint", async () => {
    const payload = { name: "New", description: "Desc", persona_prompt: "..." };
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ ...payload, id: "2" }),
      headers: new Headers({ "content-type": "application/json" }),
    });

    const result = await apiService.createAgentBlueprint(payload);
    expect(result.id).toBe("2");
  });

  test("deleteAgentBlueprint endpoint", async () => {
    (fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
      headers: new Headers({ "content-type": "application/json" }),
    });

    await apiService.deleteAgentBlueprint("agent-1");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8100/api/v1/agents/blueprints/agent-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
