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

/**
 * Fetch real advisor/agent context stats from the backend.
 * Falls back to an empty array if advisors are disabled or unavailable.
 */
export const fetchAgentStatus = async (): Promise<Agent[]> => {
  try {
    const res = await fetch("/api/v1/advisors/context/stats");
    if (!res.ok) {
      // Advisors may be disabled — return empty list gracefully
      // Also handle 404/500 if the service is completely missing
      if (res.status >= 400) return [];
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
 * Fetch all available ONNX voice models.
 */
export const fetchVoiceModels = async (): Promise<ModelFileInfo[]> => {
  try {
    const res = await fetch("/api/v1/models/files");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: ModelListResponse = await res.json();
    return data.models;
  } catch (error) {
    console.error("Failed to fetch voice models:", error);
    return [];
  }
};

/**
 * Upload a new voice model file.
 */
export const uploadVoiceModel = async (
  file: File,
  state?: "idle" | "computer" | "chatty"
): Promise<void> => {
  const formData = new FormData();
  formData.append("file", file);
  if (state) {
    formData.append("state", state);
  }

  const res = await fetch("/api/v1/models/upload", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
};

/**
 * Delete a voice model file.
 */
export const deleteVoiceModel = async (filename: string): Promise<void> => {
  const res = await fetch(`/api/v1/models/files/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Deletion failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
};
