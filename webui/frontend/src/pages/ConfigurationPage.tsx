import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Save as SaveIcon,
  Settings as SettingsIcon,
  Sliders as SlidersIcon,
  Cpu as CpuIcon,
  RefreshCw as RefreshIcon,
} from "lucide-react";
import { fetchLLMModels } from "../services/api";

// ─── Types ────────────────────────────────────────────────────────────────────
interface AppConfig {
  apiKey: string;
  llmBaseUrl: string;
  llmModel: string;
  enableVoice: boolean;
  theme: string;
}

// ─── API helpers ──────────────────────────────────────────────────────────────
async function loadConfig(): Promise<AppConfig> {
  try {
    const res = await fetch("/api/v1/config");
    if (res.ok) {
      const data = await res.json();
      return {
        apiKey: data.advisors?.providers?.api_key ?? "",
        llmBaseUrl: data.advisors?.providers?.base_url ?? "https://open-litellm.fly.dev/v1",
        llmModel: data.advisors?.providers?.model ?? "",
        enableVoice: data.voice?.enabled ?? true,
        theme: data.ui?.theme ?? "dark",
      };
    }
  } catch { /* fall through */ }
  return {
    apiKey: "",
    llmBaseUrl: "https://open-litellm.fly.dev/v1",
    llmModel: "",
    enableVoice: true,
    theme: "dark",
  };
}

async function persistConfig(cfg: AppConfig): Promise<void> {
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
      voice: { enabled: cfg.enableVoice },
      ui: { theme: cfg.theme },
    }),
  });
}

// ─── Component ────────────────────────────────────────────────────────────────
const ConfigurationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<AppConfig>({
    apiKey: "",
    llmBaseUrl: "https://open-litellm.fly.dev/v1",
    llmModel: "",
    enableVoice: true,
    theme: "dark",
  });
  const [modelList, setModelList] = useState<string[]>([]);
  const [fetchingModels, setFetchingModels] = useState(false);

  // Load config on mount
  const { data: remoteConfig } = useQuery({
    queryKey: ["config"],
    queryFn: loadConfig,
  });
  useEffect(() => {
    if (remoteConfig) setConfig(remoteConfig);
  }, [remoteConfig]);

  const mutation = useMutation({
    mutationFn: persistConfig,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };
  const handleSwitch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.checked });
  };

  const handleFetchModels = async () => {
    setFetchingModels(true);
    try {
      const models = await fetchLLMModels(config.llmBaseUrl, config.apiKey || undefined);
      setModelList(models);
      if (models.length === 0) {
        setModelList(["(no models returned — check endpoint/key)"]);
      }
    } finally {
      setFetchingModels(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-primary/10 rounded-xl text-primary">
          <SettingsIcon size={32} />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Configuration
          </h2>
          <p className="text-base-content/60">Manage application settings</p>
        </div>
      </div>

      <div className="card bg-base-100 shadow-xl border border-base-content/10 overflow-visible">
        <div className="card-body p-0">

          {/* General Settings */}
          <div className="p-6 border-b border-base-content/10">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <SlidersIcon className="w-5 h-5 text-primary" />
              General Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-control w-full">
                <label className="label">
                  <span className="label-text font-medium">Theme</span>
                </label>
                <select
                  name="theme"
                  className="select select-bordered w-full"
                  value={config.theme}
                  onChange={handleChange}
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="cyberpunk">Cyberpunk</option>
                  <option value="synthwave">Synthwave</option>
                </select>
              </div>
              <div className="form-control">
                <label className="label cursor-pointer justify-start gap-4">
                  <input
                    type="checkbox"
                    className="toggle toggle-primary"
                    checked={config.enableVoice}
                    onChange={handleSwitch}
                    name="enableVoice"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium">Enable Voice Commands</span>
                    <span className="label-text-alt text-base-content/50">Microphone input</span>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* LLM Endpoint Configuration */}
          <div className="p-6 border-b border-base-content/10">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <CpuIcon className="w-5 h-5 text-secondary" />
              LLM Endpoint
            </h3>
            <div className="space-y-4">
              <div className="form-control w-full">
                <label className="label">
                  <span className="label-text font-medium">API Base URL</span>
                  <span className="label-text-alt text-base-content/40">OpenAI-compatible</span>
                </label>
                <input
                  type="url"
                  name="llmBaseUrl"
                  placeholder="https://open-litellm.fly.dev/v1"
                  className="input input-bordered w-full focus:input-secondary"
                  value={config.llmBaseUrl}
                  onChange={handleChange}
                />
                <label className="label">
                  <span className="label-text-alt text-base-content/40">
                    Free options: openrouter.ai/api/v1 · api.groq.com/openai/v1 · api.together.xyz/v1
                  </span>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">API Key</span>
                  </label>
                  <input
                    type="password"
                    name="apiKey"
                    placeholder="sk-... or Bearer token"
                    className="input input-bordered w-full"
                    value={config.apiKey}
                    onChange={handleChange}
                    autoComplete="off"
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium">Model</span>
                    <button
                      type="button"
                      className={`btn btn-xs btn-ghost gap-1 ${fetchingModels ? "loading" : ""}`}
                      onClick={handleFetchModels}
                      disabled={fetchingModels || !config.llmBaseUrl}
                      title="Fetch available models from endpoint"
                    >
                      {!fetchingModels && <RefreshIcon size={12} />}
                      {fetchingModels ? "Fetching..." : "Fetch list"}
                    </button>
                  </label>
                  {modelList.length > 0 ? (
                    <select
                      name="llmModel"
                      className="select select-bordered w-full"
                      value={config.llmModel}
                      onChange={handleChange}
                    >
                      <option value="">— select model —</option>
                      {modelList.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      name="llmModel"
                      placeholder="gpt-4o-mini · llama-3.1-8b-instant · …"
                      className="input input-bordered w-full"
                      value={config.llmModel}
                      onChange={handleChange}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Save Footer */}
          <div className="p-4 bg-base-300/50 rounded-b-xl flex justify-between items-center">
            <span className="text-xs text-base-content/40">
              {mutation.isSuccess && "✓ Saved"}
              {mutation.isError && "✗ Save failed"}
            </span>
            <button
              className={`btn btn-primary gap-2 ${mutation.isPending ? "loading" : ""}`}
              onClick={() => mutation.mutate(config)}
              disabled={mutation.isPending}
            >
              <SaveIcon size={20} />
              {mutation.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ConfigurationPage;
