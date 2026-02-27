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

export interface CommandDefinition {
  id: string; // Internal ID for React keys
  name: string; // The config key (unique)
  displayName: string;
  actionType: string;
  description?: string;
  payload?: Record<string, any>;
  apiEnabled: boolean;
  wakewords?: any[]; // For backward compatibility or future enhancement
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
 * Fetch all commands from the backend.
 */
export const fetchCommands = async (): Promise<CommandDefinition[]> => {
  try {
    const res = await fetch("/api/v1/commands");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json(); // returns dict { name: config }

    // Map dictionary to array of CommandDefinition
    return Object.entries(data).map(([name, config]: [string, any]) => {
      // Extract known fields, put rest in payload
      const { action, description, ...rest } = config;

      // Determine a payload for display if needed
      let payload = { ...rest };

      return {
        id: name, // internal ID for React keys
        name: name,
        displayName: name, // Could be enhanced later
        actionType: action,
        description: description,
        payload: payload,
        apiEnabled: true, // Assuming all commands are API callable
        wakewords: [] // Backend doesn't link wakewords to commands directly in the same config structure yet
      } as CommandDefinition;
    });
  } catch (error) {
    console.error("Failed to fetch commands:", error);
    return [];
  }
};

/**
 * Create or update a command.
 */
export const saveCommand = async (command: Partial<CommandDefinition> & { name: string; action: string }): Promise<void> => {
  const res = await fetch("/api/v1/commands", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(command),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
};

/**
 * Delete a command.
 */
export const deleteCommand = async (commandName: string): Promise<void> => {
  const res = await fetch(`/api/v1/commands/${encodeURIComponent(commandName)}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
};
