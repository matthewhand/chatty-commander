// API service for agent/advisor status
// Connects to the real FastAPI backend

export interface Agent {
  id: string;
  name: string;
  status: "online" | "offline" | "error" | "processing";
  lastMessageSent: string;
  lastMessageReceived: string;
  lastMessageContent: string;
  error?: string;
}

// ─── Config Types ─────────────────────────────────────────────────────────────
export interface CommandAction {
  action: "keypress" | "url" | "shell" | "custom_message" | "voice_chat";
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
  [key: string]: any;
}

export interface AppConfig {
  apiKey: string;
  llmBaseUrl: string;
  llmModel: string;
  theme: string;
  envOverrides: {
    apiKey: boolean;
    baseUrl: boolean;
    model: boolean;
  };
  services: {
    voiceCommands: boolean;
    restApi: boolean;
  };
  commands: Record<string, CommandAction>;
}

/**
 * Fetch real advisor/agent context stats from the backend.
 * Falls back to an empty array if advisors are disabled or unavailable.
 */
export const fetchAgentStatus = async (): Promise<Agent[]> => {
  try {
    const res = await fetch("/api/v1/advisors/context/stats");
    if (!res.ok) {
      // Advisors may be disabled — return empty list gracefully
      if (res.status === 400 || res.status === 503) return [];
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    // data is typically { contexts: { [key]: { persona_id, platform, ... } }, total: N }
    if (!data || !data.contexts) return [];
    return Object.entries(data.contexts).map(([key, ctx]: [string, any]) => ({
      id: key,
      name: `${ctx.persona_id ?? "advisor"} @ ${key}`,
      status: "online" as const,
      lastMessageSent: ctx.last_updated ?? "-",
      lastMessageReceived: ctx.last_updated ?? "-",
      lastMessageContent: ctx.context_key ?? "-",
    }));
  } catch {
    return [];
  }
};

/**
 * Fetch available models from a custom LLM endpoint.
 * Returns [] if the endpoint is unavailable or errors.
 */
export const fetchLLMModels = async (
  baseUrl: string,
  apiKey?: string
): Promise<string[]> => {
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;
    const url = baseUrl.replace(/\/$/, "") + "/models";
    const res = await fetch(url, { headers });
    if (!res.ok) return [];
    const data = await res.json();
    if (data?.data && Array.isArray(data.data)) {
      return data.data.map((m: any) => m.id ?? m.name ?? String(m));
    }
    return [];
  } catch {
    return [];
  }
};

/**
 * Fetch application configuration from the backend.
 */
export const fetchConfig = async (): Promise<AppConfig> => {
  try {
    const res = await fetch("/api/v1/config");
    if (res.ok) {
      const data = await res.json();
      return {
        apiKey: data.advisors?.providers?.api_key ?? "",
        llmBaseUrl: data.advisors?.providers?.base_url ?? "http://localhost:11434/v1",
        llmModel: data.advisors?.providers?.model ?? "",
        theme: data.ui?.theme ?? "dark",
        envOverrides: {
          apiKey: data._env_overrides?.api_key ?? false,
          baseUrl: data._env_overrides?.base_url ?? false,
          model: data._env_overrides?.model ?? false,
        },
        services: {
          voiceCommands: data.services?.voiceCommands ?? data.voice?.enabled ?? true,
          restApi: data.services?.restApi ?? true,
        },
        commands: data.commands ?? {},
      };
    }
  } catch { /* fall through */ }
  // Default fallback
  return {
    apiKey: "",
    llmBaseUrl: "http://localhost:11434/v1",
    llmModel: "",
    theme: "dark",
    envOverrides: { apiKey: false, baseUrl: false, model: false },
    services: { voiceCommands: true, restApi: true },
    commands: {},
  };
};

/**
 * Save application configuration to the backend.
 */
export const saveConfig = async (cfg: AppConfig): Promise<void> => {
  await fetch("/api/v1/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      advisors: {
        providers: {
          api_key: cfg.apiKey,
          base_url: cfg.llmBaseUrl,
          model: cfg.llmModel,
        },
      },
      voice: { enabled: cfg.services.voiceCommands },
      ui: { theme: cfg.theme },
      services: { ...cfg.services },
      commands: cfg.commands, // Persist commands as well
    }),
  });
};
