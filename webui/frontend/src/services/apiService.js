/**
 * API Service for ChattyCommander Web Interface
 * Handles all HTTP requests to the backend API
 */

class ApiService {
  constructor(baseURL = "") {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  /**
   * Make HTTP request with error handling
   */
  async request(endpoint, options = {}) {
    // Inject Authorization header if auth_token exists and not already set
    const token = localStorage.getItem("auth_token");
    if (token && !(options.headers && options.headers.Authorization)) {
      if (!options.headers) options.headers = {};
      options.headers.Authorization = "Bearer " + token;
    }
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options,
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

      return await response.text();
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error("Network error: Unable to connect to the server");
      }
      throw error;
    }
  }
  /**
   * GET request
   */
  async get(endpoint, params = {}) {
    // Use window.location.origin as base if baseURL is empty
    const base = this.baseURL || window.location.origin;
    const url = new URL(`${base}${endpoint}`);
    Object.keys(params).forEach((key) => {
      if (params[key] !== undefined && params[key] !== null) {
        url.searchParams.append(key, params[key]);
      }
    });

    return this.request(url.pathname + url.search, {
      method: "GET",
    });
  }

  /**
   * POST request
   */
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, {
      method: "DELETE",
    });
  }

  // =============================================================================
  // API Endpoints
  // =============================================================================

  /**
   * Health check endpoint
   */
  async healthCheck() {
    return this.get("/health");
  }

  /**
   * Get system status
   */
  async getStatus() {
    return this.get("/api/v1/status");
  }

  /**
   * Get system configuration
   */
  async getConfig() {
    return this.get("/api/v1/config");
  }

  /**
   * Update system configuration
   */
  async updateConfig(config) {
    return this.put("/api/v1/config", config);
  }

  /**
   * Get current state information
   */
  async getState() {
    return this.get("/api/v1/state");
  }

  /**
   * Change system state
   */
  async changeState(newState) {
    return this.post("/api/v1/state", { new_state: newState });
  }

  /**
   * Execute a command
   */
  async executeCommand(command, parameters = {}) {
    return this.post("/api/v1/command", {
      command,
      parameters,
    });
  }

  /**
   * Get available commands
   */
  async getCommands() {
    return this.get("/api/v1/commands");
  }

  /**
   * Delete a command by name
   */
  async deleteCommand(commandName) {
    return this.delete(`/api/v1/commands/${encodeURIComponent(commandName)}`);
  }

  // =============================================================================
  // Utility Methods
  // =============================================================================

  /**
   * Set base URL for API requests
   */
  setBaseURL(url) {
    this.baseURL = url;
  }

  /**
   * Set default headers
   */
  setDefaultHeaders(headers) {
    this.defaultHeaders = { ...this.defaultHeaders, ...headers };
  }

  /**
   * Set authentication token
   */
  setAuthToken(token) {
    this.setDefaultHeaders({
      Authorization: `Bearer ${token}`,
    });
  }

  /**
   * Clear authentication token
   */
  clearAuthToken() {
    delete this.defaultHeaders["Authorization"];
  }

  /**
   * Check if server is reachable
   */
  async isServerReachable() {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get API version
   */
  async getVersion() {
    try {
      const status = await this.getStatus();
      return status.version || "unknown";
    } catch {
      return "unknown";
    }
  }

  /**
   * Ping server
   */
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
export default apiService;
