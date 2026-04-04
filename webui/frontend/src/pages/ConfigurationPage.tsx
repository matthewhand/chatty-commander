import React, { useState, useEffect, useCallback } from "react";
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
  Trash2 as TrashIcon,
  Upload as UploadIcon,
  FileAudio as FileAudioIcon,
  Copy as CopyIcon,
  Check as CheckIcon,
} from "lucide-react";
import { fetchLLMModels, fetchVoiceModels, uploadVoiceModel, deleteVoiceModel, ModelFileInfo } from "../services/api";
import { useTheme } from "../components/ThemeProvider";
import {
  Button,
  Card,
  Select,
  Toggle,
  Input,
  Alert,
  Badge,
  Progress,
  LoadingSpinner,
} from "../components/DaisyUI";

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
  useEffect(() => {
    document.title = "Configuration | ChattyCommander";
  }, []);

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
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = useCallback((field: string, value: string) => {
    navigator.clipboard.writeText(value).then(() => {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    });
  }, []);

  const { data: voiceStatus, refetch: refetchVoice } = useQuery({
    queryKey: ['voiceStatus'],
    queryFn: () => fetch('/api/voice/status').then(r => r.json()),
    refetchInterval: 5000,
  });

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

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setConfig((prev) => ({ ...prev, [name]: value }));
    if (name === "theme") {
      setTheme(value);
    }
  }, [setTheme]);

  const handleServiceSwitch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      services: {
        ...prev.services,
        [name]: checked,
      },
    }));
  }, []);

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

      <Card className="shadow-xl border border-base-content/10 overflow-visible">
        <Card.Body className="card-body p-0">

          {/* General Settings */}
          <div className="p-6 border-b border-base-content/10">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <SlidersIcon className="w-5 h-5 text-primary" />
              General Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-control w-full">
                <label className="label" htmlFor="config-theme">
                  <span className="label-text font-medium">Theme</span>
                </label>
                <Select
                  id="config-theme"
                  name="theme"
                  value={config.theme}
                  onChange={handleChange}
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="cyberpunk">Cyberpunk</option>
                  <option value="synthwave">Synthwave</option>
                </Select>
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
                  <Toggle
                    color="info"
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
                  <Toggle
                    color="info"
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
              <Card className="shadow-sm border border-base-content/10">
                <Card.Body className="card-body p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="card-title text-sm text-primary">
                        <MicIcon size={16} /> Input Device
                      </h4>
                      <p className="text-xs opacity-70">Microphone source</p>
                    </div>
                    <Button
                      variant="primary"
                      size="xs"
                      buttonStyle="outline"
                      onClick={handleTestMic}
                      disabled={isTestingMic || !inputDevice}
                    >
                      {isTestingMic ? "Testing..." : "Test"}
                    </Button>
                  </div>

                  <Select
                    size="sm"
                    variant="primary"
                    className="mb-4"
                    value={inputDevice}
                    onChange={(e) => setInputDevice(e.target.value)}
                  >
                    <option value="" disabled>Select device...</option>
                    {devices?.input.map((dev: string) => (
                      <option key={dev} value={dev}>{dev}</option>
                    ))}
                  </Select>

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
                </Card.Body>
              </Card>

              {/* Output Device Card */}
              <Card className="shadow-sm border border-base-content/10">
                <Card.Body className="card-body p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="card-title text-sm text-secondary">
                        <VolumeUpIcon size={16} className={isTestingOutput ? "animate-bounce" : ""} /> Output Device
                      </h4>
                      <p className="text-xs opacity-70">Playback endpoint</p>
                    </div>
                    <Button
                      variant="secondary"
                      size="xs"
                      buttonStyle="outline"
                      onClick={handleTestOutput}
                      disabled={isTestingOutput || !outputDevice}
                    >
                      {isTestingOutput ? "Playing..." : "Test"}
                    </Button>
                  </div>

                  <Select
                    size="sm"
                    variant="secondary"
                    className="mb-4"
                    value={outputDevice}
                    onChange={(e) => setOutputDevice(e.target.value)}
                  >
                    <option value="" disabled>Select device...</option>
                    {devices?.output.map((dev: string) => (
                      <option key={dev} value={dev}>{dev}</option>
                    ))}
                  </Select>

                  <div className="h-6 bg-base-200 rounded flex items-center justify-center px-4 overflow-hidden">
                    <span className="text-[10px] text-base-content/40 italic">
                      {isTestingOutput ? "\uD83D\uDD0A Playing test sound..." : "Ready"}
                    </span>
                  </div>
                </Card.Body>
              </Card>
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
                                <Badge
                                  size="small"
                                  variant={
                                    model.state === 'idle' ? 'primary' :
                                    model.state === 'computer' ? 'secondary' : 'neutral'
                                  }
                                  className={model.state !== 'idle' && model.state !== 'computer' ? 'badge-accent' : ''}
                                >
                                  {model.state}
                                </Badge>
                              ) : (
                                <span className="opacity-50">-</span>
                              )}
                            </td>
                            <td className="text-xs opacity-70">{model.size_human}</td>
                            <td className="text-right">
                              <Button
                                variant="ghost"
                                size="xs"
                                className="text-error"
                                onClick={() => deleteMutation.mutate(model.name)}
                                title="Delete Model"
                                aria-label={`Delete model ${model.name}`}
                                disabled={deleteMutation.isPending}
                              >
                                {deleteMutation.isPending && deleteMutation.variables === model.name ? (
                                  <LoadingSpinner size="xs" />
                                ) : (
                                  <TrashIcon size={14} />
                                )}
                              </Button>
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

              <Card className="bg-base-200/50 border border-base-content/5 h-fit">
                <Card.Body className="p-4">
                   <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                    <UploadIcon size={14}/> Upload Model
                   </h4>

                   <div className="form-control w-full mb-3">
                     <label className="label py-1">
                       <span className="label-text-alt">Target State</span>
                     </label>
                     <Select
                      size="xs"
                      value={uploadState}
                      onChange={(e) => setUploadState(e.target.value as "idle" | "computer" | "chatty")}
                     >
                       <option value="idle">Idle (Wake Word)</option>
                       <option value="computer">Computer (Active)</option>
                       <option value="chatty">Chatty (Conv.)</option>
                     </Select>
                   </div>

                   <div className="form-control w-full">
                     <input
                      type="file"
                      accept=".onnx"
                      aria-label="Select ONNX voice model file"
                      className="file-input file-input-bordered file-input-primary file-input-sm w-full"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                     />
                     <label className="label py-1">
                       <span className="label-text-alt text-warning">.onnx files only</span>
                     </label>
                   </div>

                   {isUploading && <Progress variant="primary" indeterminate className="w-full mt-2" />}
                   {uploadError && (
                     <Alert status="error" className="text-xs mt-2 py-2">
                       <span>{uploadError}</span>
                     </Alert>
                   )}
                   {deleteError && (
                     <Alert status="error" className="text-xs mt-2 py-2">
                       <span>{deleteError}</span>
                     </Alert>
                   )}
                </Card.Body>
              </Card>
            </div>
          </div>

          {/* Voice Pipeline Controls */}
          <div className="p-6 border-b border-base-content/10 bg-base-200/30">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <MicIcon className="w-5 h-5 text-success" />
              Voice Pipeline
              <Badge variant={voiceStatus?.running ? 'success' : 'ghost'} size="small">
                {voiceStatus?.running ? 'Active' : 'Inactive'}
              </Badge>
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-base-content/70">Enable real-time voice command detection</p>
                {voiceStatus?.wake_words?.length > 0 && (
                  <p className="text-xs text-base-content/50 mt-1">
                    Wake words: {voiceStatus.wake_words.join(', ')}
                  </p>
                )}
              </div>
              <Toggle
                checked={voiceStatus?.running || false}
                onChange={async () => {
                  const endpoint = voiceStatus?.running ? '/api/voice/stop' : '/api/voice/start';
                  await fetch(endpoint, { method: 'POST' });
                  refetchVoice();
                }}
                color="success"
              />
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
                <label className="label" htmlFor="config-llm-base-url">
                  <span className="label-text font-medium text-base-content flex items-center gap-2">
                    API Base URL {config.envOverrides.baseUrl && <Badge variant="error" size="small">LOCKED BY ENV</Badge>}
                  </span>
                  <span className="label-text-alt text-base-content/40">OpenAI-compatible</span>
                </label>
                <div className="flex gap-1 items-center">
                  <Input
                    id="config-llm-base-url"
                    type="url"
                    name="llmBaseUrl"
                    placeholder={config.envOverrides.baseUrl ? "(Configured via environment variable)" : "http://localhost:11434/v1"}
                    className="focus:input-secondary disabled:opacity-50"
                    value={config.envOverrides.baseUrl ? "################" : config.llmBaseUrl}
                    onChange={handleChange}
                    disabled={config.envOverrides.baseUrl}
                  />
                  {!config.envOverrides.baseUrl && (
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => handleCopy("baseUrl", config.llmBaseUrl)}
                      title="Copy to clipboard"
                      aria-label="Copy API Base URL"
                    >
                      {copiedField === "baseUrl" ? <CheckIcon size={14} className="text-success" /> : <CopyIcon size={14} />}
                    </Button>
                  )}
                </div>
                <label className="label">
                  <span className="label-text-alt text-base-content/40">
                    Free options: openrouter.ai/api/v1 · api.groq.com/openai/v1 · api.together.xyz/v1
                  </span>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-control w-full">
                  <label className="label" htmlFor="config-api-key">
                    <span className="label-text font-medium flex items-center gap-2">
                      API Key {config.envOverrides.apiKey && <Badge variant="error" size="small">LOCKED BY ENV</Badge>}
                    </span>
                  </label>
                  <Input
                    id="config-api-key"
                    type="password"
                    name="apiKey"
                    placeholder={config.envOverrides.apiKey ? "(Configured via environment variable)" : "sk-... or Bearer token"}
                    className="disabled:opacity-50"
                    value={config.envOverrides.apiKey ? "********" : config.apiKey}
                    onChange={handleChange}
                    autoComplete="off"
                    disabled={config.envOverrides.apiKey}
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label" htmlFor="config-model">
                    <span className="label-text font-medium flex items-center gap-2">
                      Model {config.envOverrides.model && <Badge variant="error" size="small">LOCKED BY ENV</Badge>}
                    </span>
                    <Button
                      variant="ghost"
                      size="xs"
                      className="gap-1"
                      onClick={handleFetchModels}
                      disabled={fetchingModels || !config.llmBaseUrl || config.envOverrides.baseUrl || config.envOverrides.model}
                      title="Fetch available models from endpoint"
                    >
                      {fetchingModels ? <LoadingSpinner size="xs" /> : <RefreshIcon size={12} />}
                      {fetchingModels ? "Fetching..." : "Fetch list"}
                    </Button>
                  </label>
                  {modelList.length > 0 && !config.envOverrides.model ? (
                    <div className="flex gap-1 items-center">
                      <Select
                        id="config-model"
                        name="llmModel"
                        value={config.llmModel}
                        onChange={handleChange}
                      >
                        <option value="">-- select model --</option>
                        {modelList.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </Select>
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => handleCopy("model", config.llmModel)}
                        title="Copy to clipboard"
                        aria-label="Copy Model"
                      >
                        {copiedField === "model" ? <CheckIcon size={14} className="text-success" /> : <CopyIcon size={14} />}
                      </Button>
                    </div>
                  ) : (
                    <div className="flex gap-1 items-center">
                      <Input
                        id="config-model"
                        type="text"
                        name="llmModel"
                        placeholder={config.envOverrides.model ? "(Configured via environment variable)" : "gpt-4o-mini · llama-3.1-8b-instant · ..."}
                        className="disabled:opacity-50"
                        value={config.envOverrides.model ? "################" : config.llmModel}
                        onChange={handleChange}
                        disabled={config.envOverrides.model}
                      />
                      {!config.envOverrides.model && (
                        <Button
                          variant="ghost"
                          size="xs"
                          onClick={() => handleCopy("model", config.llmModel)}
                          title="Copy to clipboard"
                          aria-label="Copy Model"
                        >
                          {copiedField === "model" ? <CheckIcon size={14} className="text-success" /> : <CopyIcon size={14} />}
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Save Footer */}
          <div className="p-4 bg-base-300/50 rounded-b-xl flex justify-between items-center">
            <span className="text-xs text-base-content/40">
              {mutation.isSuccess && "\u2713 Saved"}
              {mutation.isError && "\u2717 Save failed"}
            </span>
            <Button
              variant="primary"
              className="gap-2"
              onClick={() => mutation.mutate(config)}
              loading={mutation.isPending}
              loadingText="Saving..."
              icon={<SaveIcon size={20} />}
            >
              Save Changes
            </Button>
          </div>

        </Card.Body>
      </Card>
    </div>
  );
};

export default ConfigurationPage;
