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
    const url = new URL(`${this.baseURL}${endpoint}`);
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
    return this.get("/api/status");
  }

  /**
   * Get system configuration
   */
  async getConfig() {
    return this.get("/api/config");
  }

  /**
   * Update system configuration
   */
  async updateConfig(config) {
    return this.put("/api/config", config);
  }

  /**
   * Get current state information
   */
  async getState() {
    return this.get("/api/state");
  }

  /**
   * Change system state
   */
  async changeState(newState) {
    return this.post("/api/state", { new_state: newState });
  }

  /**
   * Execute a command
   */
  async executeCommand(command, parameters = {}) {
    return this.post("/api/command", {
      command,
      parameters,
    });
  }

  /**
   * Get available commands
   */
  async getCommands() {
    return this.get("/api/commands");
  }

  /**
   * Get command history
   */
  async getCommandHistory(limit = 50) {
    return this.get("/api/commands/history", { limit });
  }

  /**
   * Get system logs
   */
  async getLogs(level = "info", limit = 100) {
    return this.get("/api/logs", { level, limit });
  }

  /**
   * Get model information
   */
  async getModels() {
    return this.get("/api/models");
  }

  /**
   * Load a specific model
   */
  async loadModel(modelPath, modelType = "general") {
    return this.post("/api/models/load", {
      model_path: modelPath,
      model_type: modelType,
    });
  }

  /**
   * Unload a model
   */
  async unloadModel(modelPath) {
    return this.post("/api/models/unload", {
      model_path: modelPath,
    });
  }

  /**
   * Get audio devices
   */
  async getAudioDevices() {
    return this.get("/api/audio/devices");
  }

  /**
   * Set audio input device
   */
  async setAudioDevice(deviceId) {
    return this.post("/api/audio/device", {
      device_id: deviceId,
    });
  }

  /**
   * Start voice recognition
   */
  async startVoiceRecognition() {
    return this.post("/api/voice/start");
  }

  /**
   * Stop voice recognition
   */
  async stopVoiceRecognition() {
    return this.post("/api/voice/stop");
  }

  /**
   * Get voice recognition status
   */
  async getVoiceStatus() {
    return this.get("/api/voice/status");
  }

  /**
   * Test command execution (dry run)
   */
  async testCommand(command, parameters = {}) {
    return this.post("/api/command/test", {
      command,
      parameters,
    });
  }

  /**
   * Get system metrics
   */
  async getMetrics() {
    return this.get("/api/metrics");
  }

  /**
   * Export configuration
   */
  async exportConfig() {
    return this.get("/api/config/export");
  }

  /**
   * Import configuration
   */
  async importConfig(configData) {
    return this.post("/api/config/import", configData);
  }

  /**
   * Reset configuration to defaults
   */
  async resetConfig() {
    return this.post("/api/config/reset");
  }

  /**
   * Validate configuration
   */
  async validateConfig(config) {
    return this.post("/api/config/validate", config);
  }

  /**
   * Get available themes
   */
  async getThemes() {
    return this.get("/api/themes");
  }

  /**
   * Set UI theme
   */
  async setTheme(themeName) {
    return this.post("/api/theme", { theme: themeName });
  }

  /**
   * Get user preferences
   */
  async getPreferences() {
    return this.get("/api/preferences");
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences) {
    return this.put("/api/preferences", preferences);
  }

  /**
   * Backup system data
   */
  async createBackup() {
    return this.post("/api/backup");
  }

  /**
   * Restore from backup
   */
  async restoreBackup(backupData) {
    return this.post("/api/restore", backupData);
  }

  /**
   * Get system information
   */
  async getSystemInfo() {
    return this.get("/api/system/info");
  }

  /**
   * Restart system
   */
  async restartSystem() {
    return this.post("/api/system/restart");
  }

  /**
   * Shutdown system
   */
  async shutdownSystem() {
    return this.post("/api/system/shutdown");
  }

  /**
   * Update system
   */
  async updateSystem() {
    return this.post("/api/system/update");
  }

  /**
   * Check for updates
   */
  async checkUpdates() {
    return this.get("/api/system/updates");
  }

  /**
   * Get advisor personas
   */
  async getAdvisorPersonas() {
    return this.get("/api/v1/advisors/personas");
  }

  /**
   * Get advisors context stats
   */
  async getAdvisorContextStats() {
    return this.get("/api/v1/advisors/context/stats");
  }

  /**
   * Switch advisor persona for a context
   */
  async switchAdvisorPersona(contextKey, personaId) {
    const url = new URL(`${this.baseURL}/api/v1/advisors/context/switch`);
    url.searchParams.append("context_key", contextKey);
    url.searchParams.append("persona_id", personaId);
    return this.post(url.pathname + url.search, {});
  }

  /**
   * Get advisor memory items for a context
   */
  async getAdvisorMemory({ platform, channel, user, limit = 20 }) {
    return this.get("/api/v1/advisors/memory", {
      platform,
      channel,
      user,
      limit,
    });
  }

  /**
   * Clear advisor memory for a context
   */
  async clearAdvisorMemory({ platform, channel, user }) {
    return this.delete(
      `/api/v1/advisors/memory?platform=${encodeURIComponent(platform)}&channel=${encodeURIComponent(channel)}&user=${encodeURIComponent(user)}`,
    );
  }

  /**
   * Send message to advisors
   */
  async sendAdvisorMessage({
    platform,
    channel,
    user,
    text,
    username,
    metadata,
  }) {
    return this.post("/api/v1/advisors/message", {
      platform,
      channel,
      user,
      text,
      username,
      metadata,
    });
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
