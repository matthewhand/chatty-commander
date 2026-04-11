/**
 * API Service for ChattyCommander Web Interface
 * Handles all HTTP requests to the backend API
 */

export interface Agent {
  id: string;
  name: string;
  status: "online" | "offline" | "error" | "processing";
  lastMessageSent: string;
  lastMessageReceived: string;
  lastMessageContent: string;
  error?: string;
}

export interface ModelFileInfo {
  name: string;
  path: string;
  size_bytes: number;
  size_human: string;
  modified: string;
  state: "idle" | "computer" | "chatty" | null;
}

export interface ModelListResponse {
  models: ModelFileInfo[];
  total_count: number;
  total_size_bytes: number;
  total_size_human: string;
}

export interface AgentBlueprint {
  id: string;
  name: string;
  description: string;
  persona_prompt: string;
  capabilities: string[];
  team_role: string | null;
  handoff_triggers: string[];
}

export interface CreateAgentPayload {
  name: string;
  description: string;
  persona_prompt: string;
  capabilities?: string[];
  team_role?: string | null;
  handoff_triggers?: string[];
}

class ApiService {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseURL = "") {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  /**
   * Make HTTP request with error handling
   */
  async request<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Inject Authorization header if auth_token exists and not already set
    const token = localStorage.getItem("auth_token");
    if (token && !(options.headers && (options.headers as any).Authorization)) {
      if (!options.headers) options.headers = {};
      (options.headers as any).Authorization = "Bearer " + token;
    }
    
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: { ...this.defaultHeaders, ...options.headers },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail ||
          errorData.message ||
          `HTTP ${response.status}: ${response.statusText}`,
        );
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }

      return (await response.text()) as unknown as T;
    } catch (error: any) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error("Network error: Unable to connect to the server");
      }
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, params: Record<string, any> = {}): Promise<T> {
    const url = new URL(endpoint.startsWith("http") ? endpoint : `${this.baseURL || window.location.origin}${endpoint}`);
    Object.keys(params).forEach((key) => {
      if (params[key] !== undefined && params[key] !== null) {
        url.searchParams.append(key, params[key]);
      }
    });

    const target = endpoint.startsWith("http") ? url.toString() : url.pathname + url.search;
    return this.request<T>(target, {
      method: "GET",
    });
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, data: any = {}): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, data: any = {}): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: "DELETE",
    });
  }

  // =============================================================================
  // API Endpoints
  // =============================================================================

  async healthCheck() {
    return this.get("/health");
  }

  async getStatus() {
    return this.get("/api/v1/status");
  }

  async getConfig() {
    return this.get("/api/v1/config");
  }

  async updateConfig(config: any) {
    return this.put("/api/v1/config", config);
  }

  async getState() {
    return this.get("/api/v1/state");
  }

  async changeState(newState: string) {
    return this.post("/api/v1/state", { new_state: newState });
  }

  async executeCommand(command: string, parameters = {}) {
    return this.post("/api/v1/command", {
      command,
      parameters,
    });
  }

  async getCommands() {
    return this.get<Record<string, any>>("/api/v1/commands");
  }

  async deleteCommand(commandName: string) {
    return this.delete(`/api/v1/commands/${encodeURIComponent(commandName)}`);
  }

  // --- Re-implemented from api.ts using the common request handler ---

  async fetchAgentStatus(): Promise<Agent[]> {
    try {
      const data = await this.get("/api/v1/advisors/context/stats");
      if (!data || !data.contexts) return [];
      return Object.entries(data.contexts as Record<string, Record<string, unknown>>).map(([key, ctx]) => ({
        id: key,
        name: `${String(ctx.persona_id ?? "advisor")} @ ${key}`,
        status: "online" as const,
        lastMessageSent: String(ctx.last_updated ?? "-"),
        lastMessageReceived: String(ctx.last_updated ?? "-"),
        lastMessageContent: String(ctx.context_key ?? "-"),
      }));
    } catch {
      return [];
    }
  }

  async fetchLLMModels(baseUrl: string, apiKey?: string): Promise<string[]> {
    try {
      const headers: Record<string, string> = {};
      if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;
      
      const url = baseUrl.replace(/\/$/, "") + "/models";
      const data = await this.get<any>(url, { headers });
      
      if (data?.data && Array.isArray(data.data)) {
        return data.data.map((m: Record<string, unknown> | string) => {
          if (typeof m === 'string') return m;
          return String(m.id ?? m.name ?? String(m));
        });
      }
      return [];
    } catch {
      return [];
    }
  }

  async fetchVoiceModels(): Promise<ModelFileInfo[]> {
    try {
      const data = await this.get<ModelListResponse>("/api/v1/models/files");
      return data.models;
    } catch {
      return [];
    }
  }

  async uploadVoiceModel(file: File, state?: "idle" | "computer" | "chatty"): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);
    if (state) formData.append("state", state);
    return this.post("/api/v1/models/upload", formData);
  }

  async deleteVoiceModel(filename: string): Promise<void> {
    return this.delete(`/api/v1/models/files/${encodeURIComponent(filename)}`);
  }

  async fetchAgentBlueprints(): Promise<AgentBlueprint[]> {
    return this.get<AgentBlueprint[]>('/api/v1/agents/blueprints');
  }

  async createAgentBlueprint(data: CreateAgentPayload): Promise<AgentBlueprint> {
    return this.post<AgentBlueprint>('/api/v1/agents/blueprints', data);
  }

  async deleteAgentBlueprint(agentId: string): Promise<void> {
    return this.delete(`/api/v1/agents/blueprints/${encodeURIComponent(agentId)}`);
  }

  // =============================================================================
  // Utility Methods
  // =============================================================================

  setBaseURL(url: string) {
    this.baseURL = url;
  }

  setDefaultHeaders(headers: Record<string, string>) {
    this.defaultHeaders = { ...this.defaultHeaders, ...headers };
  }

  setAuthToken(token: string) {
    this.setDefaultHeaders({
      Authorization: `Bearer ${token}`,
    });
  }

  clearAuthToken() {
    const newHeaders = { ...this.defaultHeaders };
    delete newHeaders["Authorization"];
    this.defaultHeaders = newHeaders;
  }

  async isServerReachable() {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }

  async getVersion() {
    try {
      const status = await this.getStatus();
      return status.version || "unknown";
    } catch {
      return "unknown";
    }
  }

  async ping() {
    const start = Date.now();
    try {
      await this.healthCheck();
      return Date.now() - start;
    } catch {
      return -1;
    }
  }
}

// Create and export singleton instance
export const apiService = new ApiService();

// Standalone functional exports for backward compatibility with api.ts callers
export const fetchAgentStatus = () => apiService.fetchAgentStatus();
export const fetchLLMModels = (baseUrl: string, apiKey?: string) => apiService.fetchLLMModels(baseUrl, apiKey);
export const fetchVoiceModels = () => apiService.fetchVoiceModels();
export const uploadVoiceModel = (file: File, state?: "idle" | "computer" | "chatty") => apiService.uploadVoiceModel(file, state);
export const deleteVoiceModel = (filename: string) => apiService.deleteVoiceModel(filename);
export const fetchAgentBlueprints = () => apiService.fetchAgentBlueprints();
export const createAgentBlueprint = (data: CreateAgentPayload) => apiService.createAgentBlueprint(data);
export const deleteAgentBlueprint = (agentId: string) => apiService.deleteAgentBlueprint(agentId);

export default apiService;
