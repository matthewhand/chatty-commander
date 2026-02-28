import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Save as SaveIcon,
  Settings as SettingsIcon,
  Sliders as SlidersIcon,
  Cpu as CpuIcon,
  RefreshCw as RefreshIcon,
  Mic as MicIcon,
  Volume2 as VolumeUpIcon,
  Headphones as HeadphonesIcon,
  Server as ServerIcon,
  Activity as ActivityIcon,
  Trash2 as TrashIcon,
  Upload as UploadIcon,
  FileAudio as FileAudioIcon,
} from "lucide-react";
import { fetchLLMModels, fetchVoiceModels, uploadVoiceModel, deleteVoiceModel, ModelFileInfo } from "../services/api";
import { useTheme } from "../components/ThemeProvider";

// ─── Types ────────────────────────────────────────────────────────────────────
interface AppConfig {
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
}

// ─── API helpers ──────────────────────────────────────────────────────────────
async function loadConfig(): Promise<AppConfig> {
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
      };
    }
  } catch { /* fall through */ }
  return {
    apiKey: "",
    llmBaseUrl: "http://localhost:11434/v1",
    llmModel: "",
    theme: "dark",
    envOverrides: { apiKey: false, baseUrl: false, model: false },
    services: { voiceCommands: true, restApi: true },
  };
}

const getAudioDevices = async () => {
  try {
    const res = await fetch("/api/v1/audio/devices");
    if (res.ok) return await res.json() as { input: string[]; output: string[] };
  } catch { /* ignore */ }
  return { input: [] as string[], output: [] as string[] };
};

const saveAudioSettings = async (settings: { inputDevice: string; outputDevice: string }) => {
  await fetch("/api/v1/audio/device", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: settings.inputDevice }),
  });
};

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
      voice: { enabled: cfg.services.voiceCommands },
      ui: { theme: cfg.theme },
      services: { ...cfg.services },
    }),
  });
}

// ─── Component ────────────────────────────────────────────────────────────────
const ConfigurationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { setTheme } = useTheme();
  const [config, setConfig] = useState<AppConfig>({
    apiKey: "",
    llmBaseUrl: "http://localhost:11434/v1",
    llmModel: "",
    theme: "dark",
    envOverrides: { apiKey: false, baseUrl: false, model: false },
    services: { voiceCommands: true, restApi: true },
  });
  const [modelList, setModelList] = useState<string[]>([]);
  const [fetchingModels, setFetchingModels] = useState(false);

  // Audio state
  const [inputDevice, setInputDevice] = useState("");
  const [outputDevice, setOutputDevice] = useState("");
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [isTestingOutput, setIsTestingOutput] = useState(false);

  // Voice Models State
  const [uploadState, setUploadState] = useState<"idle" | "computer" | "chatty">("idle");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: devices } = useQuery({
    queryKey: ["audioDevices"],
    queryFn: getAudioDevices,
  });

  const { data: voiceModels, refetch: refetchVoiceModels } = useQuery({
    queryKey: ["voiceModels"],
    queryFn: fetchVoiceModels,
  });

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
      // also save audio settings
      if (inputDevice || outputDevice) {
        saveAudioSettings({ inputDevice, outputDevice });
      }
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ file, state }: { file: File; state: "idle" | "computer" | "chatty" }) => {
      await uploadVoiceModel(file, state);
    },
    onSuccess: () => {
      refetchVoiceModels();
      setIsUploading(false);
      setUploadError(null);
    },
    onError: (err: unknown) => {
      setIsUploading(false);
      setUploadError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteVoiceModel,
    onSuccess: () => {
      refetchVoiceModels();
      setDeleteError(null);
    },
    onError: (err: unknown) => {
      setDeleteError(err instanceof Error ? err.message : "Delete failed. Please try again.");
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setIsUploading(true);
      setUploadError(null);
      uploadMutation.mutate({ file, state: uploadState });
      // Reset input only after mutation completes (in onSuccess/onError)
      // to allow retry with the same file if needed
      e.target.value = "";
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
    if (e.target.name === "theme") {
      setTheme(e.target.value);
    }
  };
  const handleSwitch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.checked });
  };
  const handleServiceSwitch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({
      ...config,
      services: {
        ...config.services,
        [e.target.name]: e.target.checked,
      },
    });
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

  const handleTestMic = () => {
    setIsTestingMic(true);
    setTimeout(() => setIsTestingMic(false), 3000); // Simulate 3s test
  };

  const handleTestOutput = () => {
    setIsTestingOutput(true);
    setTimeout(() => setIsTestingOutput(false), 2000); // Simulate 2s sound
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
            </div>
          </div>

          {/* Services Configuration */}
          <div className="p-6 border-b border-base-content/10 bg-base-200/50">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <ServerIcon className="w-5 h-5 text-info" />
              Services
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-control">
                <label className="label cursor-pointer justify-start gap-4">
                  <input
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.voiceCommands}
                    onChange={handleServiceSwitch}
                    name="voiceCommands"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">Voice Commands (always-on)</span>
                    <span className="label-text-alt text-base-content/60">Listens for audio using ONNX models via openwakeword</span>
                  </div>
                </label>
              </div>

              <div className="form-control">
                <label className="label cursor-pointer justify-start gap-4">
                  <input
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.restApi}
                    onChange={handleServiceSwitch}
                    name="restApi"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">REST API</span>
                    <span className="label-text-alt text-base-content/60">Needed for this WebUI functionality</span>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Audio Hardware Component */}
          <div className="p-6 border-b border-base-content/10 bg-base-200/30">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <HeadphonesIcon className="w-5 h-5 text-accent" />
              Audio Devices
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Input Device Card */}
              <div className="card bg-base-100 shadow-sm border border-base-content/10">
                <div className="card-body p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="card-title text-sm text-primary">
                        <MicIcon size={16} /> Input Device
                      </h4>
                      <p className="text-xs opacity-70">Microphone source</p>
                    </div>
                    <button
                      className="btn btn-xs btn-outline btn-primary"
                      onClick={handleTestMic}
                      disabled={isTestingMic || !inputDevice}
                    >
                      {isTestingMic ? "Testing..." : "Test"}
                    </button>
                  </div>

                  <select
                    className="select select-bordered select-sm w-full select-primary mb-4"
                    value={inputDevice}
                    onChange={(e) => setInputDevice(e.target.value)}
                  >
                    <option value="" disabled>Select device...</option>
                    {devices?.input.map((dev: string) => (
                      <option key={dev} value={dev}>{dev}</option>
                    ))}
                  </select>

                  {/* Visualizer Area */}
                  <div className="h-6 bg-base-200 rounded flex items-center px-4 gap-1 overflow-hidden">
                    {isTestingMic ? (
                      Array.from({ length: 15 }).map((_, i) => (
                        <div
                          key={i}
                          className="w-full bg-primary rounded-full animate-pulse"
                          style={{ height: `${Math.max(10, Math.random() * 100)}%`, animationDuration: `${0.2 + Math.random() * 0.5}s` }}
                        />
                      ))
                    ) : (
                      <span className="text-[10px] text-base-content/40 italic w-full text-center">Click Test</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Output Device Card */}
              <div className="card bg-base-100 shadow-sm border border-base-content/10">
                <div className="card-body p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="card-title text-sm text-secondary">
                        <VolumeUpIcon size={16} className={isTestingOutput ? "animate-bounce" : ""} /> Output Device
                      </h4>
                      <p className="text-xs opacity-70">Playback endpoint</p>
                    </div>
                    <button
                      className="btn btn-xs btn-outline btn-secondary"
                      onClick={handleTestOutput}
                      disabled={isTestingOutput || !outputDevice}
                    >
                      {isTestingOutput ? "Playing..." : "Test"}
                    </button>
                  </div>

                  <select
                    className="select select-bordered select-sm w-full select-secondary mb-4"
                    value={outputDevice}
                    onChange={(e) => setOutputDevice(e.target.value)}
                  >
                    <option value="" disabled>Select device...</option>
                    {devices?.output.map((dev: string) => (
                      <option key={dev} value={dev}>{dev}</option>
                    ))}
                  </select>

                  <div className="h-6 bg-base-200 rounded flex items-center justify-center px-4 overflow-hidden">
                    <span className="text-[10px] text-base-content/40 italic">
                      {isTestingOutput ? "🔊 Playing test sound..." : "Ready"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Voice Models Section */}
          <div className="p-6 border-b border-base-content/10">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <FileAudioIcon className="w-5 h-5 text-warning" />
              Voice Models (ONNX)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="col-span-2">
                <div className="overflow-x-auto bg-base-200/30 rounded-lg border border-base-content/5 max-h-60 overflow-y-auto custom-scrollbar">
                  <table className="table table-xs w-full">
                    <thead className="sticky top-0 bg-base-200 z-10">
                      <tr>
                        <th>Name</th>
                        <th>State</th>
                        <th>Size</th>
                        <th className="text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {voiceModels && voiceModels.length > 0 ? (
                        voiceModels.map((model: ModelFileInfo) => (
                          <tr key={model.name} className="hover:bg-base-200/50">
                            <td className="font-mono text-xs">{model.name}</td>
                            <td>
                              {model.state ? (
                                <span className={`badge badge-xs ${
                                  model.state === 'idle' ? 'badge-primary' :
                                  model.state === 'computer' ? 'badge-secondary' : 'badge-accent'
                                }`}>
                                  {model.state}
                                </span>
                              ) : (
                                <span className="opacity-50">-</span>
                              )}
                            </td>
                            <td className="text-xs opacity-70">{model.size_human}</td>
                            <td className="text-right">
                              <button
                                className="btn btn-ghost btn-xs text-error"
                                onClick={() => deleteMutation.mutate(model.name)}
                                title="Delete Model"
                                aria-label="Delete Model"
                                disabled={deleteMutation.isPending}
                              >
                                <TrashIcon size={14} />
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="text-center py-4 opacity-50 italic">
                            No custom models found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card bg-base-200/50 border border-base-content/5 p-4 h-fit">
                 <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                  <UploadIcon size={14}/> Upload Model
                 </h4>

                 <div className="form-control w-full mb-3">
                   <label className="label py-1">
                     <span className="label-text-alt">Target State</span>
                   </label>
                   <select
                    className="select select-bordered select-xs w-full"
                    value={uploadState}
                    onChange={(e) => setUploadState(e.target.value as "idle" | "computer" | "chatty")}
                   >
                     <option value="idle">Idle (Wake Word)</option>
                     <option value="computer">Computer (Active)</option>
                     <option value="chatty">Chatty (Conv.)</option>
                   </select>
                 </div>

                 <div className="form-control w-full">
                   <input
                    type="file"
                    accept=".onnx"
                    className="file-input file-input-bordered file-input-primary file-input-sm w-full"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                   />
                   <label className="label py-1">
                     <span className="label-text-alt text-warning">.onnx files only</span>
                   </label>
                 </div>

                 {isUploading && <progress className="progress progress-primary w-full mt-2"></progress>}
                 {uploadError && (
                   <div className="alert alert-error text-xs mt-2 py-2">
                     <span>{uploadError}</span>
                   </div>
                 )}
                 {deleteError && (
                   <div className="alert alert-error text-xs mt-2 py-2">
                     <span>{deleteError}</span>
                   </div>
                 )}
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
                  <span className="label-text font-medium text-base-content flex items-center gap-2">
                    API Base URL {config.envOverrides.baseUrl && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                  </span>
                  <span className="label-text-alt text-base-content/40">OpenAI-compatible</span>
                </label>
                <input
                  type="url"
                  name="llmBaseUrl"
                  placeholder={config.envOverrides.baseUrl ? "(Configured via environment variable)" : "http://localhost:11434/v1"}
                  className="input input-bordered w-full focus:input-secondary disabled:opacity-50"
                  value={config.envOverrides.baseUrl ? "################" : config.llmBaseUrl}
                  onChange={handleChange}
                  disabled={config.envOverrides.baseUrl}
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
                    <span className="label-text font-medium flex items-center gap-2">
                      API Key {config.envOverrides.apiKey && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                    </span>
                  </label>
                  <input
                    type="password"
                    name="apiKey"
                    placeholder={config.envOverrides.apiKey ? "(Configured via environment variable)" : "sk-... or Bearer token"}
                    className="input input-bordered w-full disabled:opacity-50"
                    value={config.envOverrides.apiKey ? "********" : config.apiKey}
                    onChange={handleChange}
                    autoComplete="off"
                    disabled={config.envOverrides.apiKey}
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-medium flex items-center gap-2">
                      Model {config.envOverrides.model && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                    </span>
                    <button
                      type="button"
                      className={`btn btn-xs btn-ghost gap-1 ${fetchingModels ? "loading" : ""}`}
                      onClick={handleFetchModels}
                      disabled={fetchingModels || !config.llmBaseUrl || config.envOverrides.baseUrl || config.envOverrides.model}
                      title="Fetch available models from endpoint"
                    >
                      {!fetchingModels && <RefreshIcon size={12} />}
                      {fetchingModels ? "Fetching..." : "Fetch list"}
                    </button>
                  </label>
                  {modelList.length > 0 && !config.envOverrides.model ? (
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
                      placeholder={config.envOverrides.model ? "(Configured via environment variable)" : "gpt-4o-mini · llama-3.1-8b-instant · …"}
                      className="input input-bordered w-full disabled:opacity-50"
                      value={config.envOverrides.model ? "################" : config.llmModel}
                      onChange={handleChange}
                      disabled={config.envOverrides.model}
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
