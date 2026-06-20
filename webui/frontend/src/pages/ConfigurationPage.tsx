import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useSearchParams } from "react-router-dom";
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
  HelpCircle as HelpIcon,
  AlertTriangle as AlertTriangleIcon,
  RotateCcw as RotateCcwIcon,
} from "lucide-react";
import { fetchLLMModels, fetchVoiceModels, uploadVoiceModel, deleteVoiceModel, ModelFileInfo } from "../services/api";
import { useTheme, AVAILABLE_THEMES } from "../components/ThemeProvider";
import { useToast } from "../components/ToastProvider";
import { runMicTest, playTestTone } from "../utils/audioTest";

// In-browser audio test tuning.
const MIC_TEST_DURATION_MS = 3000;
const OUTPUT_TONE_DURATION_MS = 1500;
/** Minimum peak level (0-100) for the mic test to count as "signal detected". */
const MIC_SIGNAL_THRESHOLD = 3;

// ─── Types ────────────────────────────────────────────────────────────────────
interface AppConfig {
  apiKey: string;
  llmBaseUrl: string;
  llmModel: string;
  theme: string;
  inputDevice: string;
  outputDevice: string;
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

// The known tab ids, in display order. Used both as the URL `?tab=` vocabulary
// and (via the derived TabId) for compile-time exhaustiveness.
const TAB_IDS = ["general", "audio", "models", "llm"] as const;
type TabId = (typeof TAB_IDS)[number];

/** Coerce an arbitrary `?tab=` value to a known tab id, defaulting to general. */
const normalizeTab = (value: string | null): TabId =>
  (TAB_IDS as readonly string[]).includes(value ?? "") ? (value as TabId) : "general";

const DEFAULT_CONFIG: AppConfig = {
  apiKey: "",
  llmBaseUrl: "http://localhost:11434/v1",
  llmModel: "",
  theme: "dark",
  inputDevice: "",
  outputDevice: "",
  envOverrides: { apiKey: false, baseUrl: false, model: false },
  services: { voiceCommands: true, restApi: true },
};

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
        inputDevice: data.audio_settings?.input_device ?? data.audio_settings?.device ?? "",
        outputDevice: data.audio_settings?.output_device ?? "",
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
  } catch (err) {
    // Surface the failure for debugging instead of silently swallowing it.
    // The caller still falls back to default config below so the UI stays usable.
    console.error("Failed to load configuration; falling back to defaults:", err);
  }
  return { ...DEFAULT_CONFIG };
}

const getAudioDevices = async () => {
  try {
    const res = await fetch("/api/v1/audio/devices");
    if (res.ok) return await res.json() as { input: string[]; output: string[] };
  } catch { /* ignore */ }
  return { input: [] as string[], output: [] as string[] };
};

async function persistConfig(cfg: AppConfig): Promise<void> {
  const res = await fetch("/api/v1/config", {
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
      // Persist BOTH audio devices server-side (previously the output device
      // selection was silently dropped — only the input was ever sent).
      audio_settings: {
        input_device: cfg.inputDevice,
        output_device: cfg.outputDevice,
      },
    }),
  });
  if (!res.ok) {
    // Pull the real error out of the response so the caller can surface it
    // instead of pretending the save succeeded (it previously never checked).
    let detail = `Request failed (HTTP ${res.status})`;
    try {
      const body = await res.json();
      detail = body?.detail || body?.error || detail;
    } catch {
      const text = await res.text().catch(() => "");
      if (text) detail = text;
    }
    throw new Error(detail);
  }
}

/** Human-readable label for a DaisyUI theme id (e.g. "nord" → "Nord"). */
const themeLabel = (id: string): string =>
  id.length ? id.charAt(0).toUpperCase() + id.slice(1) : id;

// ─── Small presentational helpers ─────────────────────────────────────────────
/** Inline tooltip help icon for technical options. */
const HelpHint: React.FC<{ text: string; label: string }> = ({ text, label }) => (
  <span className="tooltip tooltip-right align-middle" data-tip={text}>
    <HelpIcon
      size={14}
      className="text-base-content/50 cursor-help"
      role="img"
      aria-label={label}
    />
  </span>
);

// ─── Component ────────────────────────────────────────────────────────────────
const ConfigurationPage: React.FC = () => {
  useEffect(() => {
    document.title = "Configuration | ChattyCommander";
  }, []);

  const queryClient = useQueryClient();
  const { setTheme } = useTheme();
  const { addToast } = useToast();

  const [config, setConfig] = useState<AppConfig>({ ...DEFAULT_CONFIG });
  // The last-known remote/loaded config; the source of truth for dirtiness.
  const [baseline, setBaseline] = useState<AppConfig>({ ...DEFAULT_CONFIG });

  // Back the active tab with the URL (?tab=) so it survives refresh/back and can
  // be deep-linked/shared. An unknown or missing value falls back to "general".
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = normalizeTab(searchParams.get("tab"));
  const setActiveTab = useCallback(
    (tab: TabId) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set("tab", tab);
          return next;
        },
        // Replace (not push) so flipping tabs doesn't flood the history stack
        // and the browser Back button still leaves the page in one press.
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const [modelList, setModelList] = useState<string[]>([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [modelFetchError, setModelFetchError] = useState<string | null>(null);

  // In-browser audio test state. The mic test measures real input levels via
  // getUserMedia + AnalyserNode; the output test plays a generated tone.
  const [micTestStatus, setMicTestStatus] = useState<"idle" | "testing" | "done" | "error">("idle");
  const [micLevel, setMicLevel] = useState(0);
  const [micPeak, setMicPeak] = useState(0);
  const [micTestError, setMicTestError] = useState<string | null>(null);
  const [outputTestStatus, setOutputTestStatus] = useState<"idle" | "playing" | "done" | "error">("idle");
  const [outputTestError, setOutputTestError] = useState<string | null>(null);
  // Handle to the in-progress mic-test MediaStream. runMicTest owns its own
  // stream internally and releases it when its timer elapses, but if the user
  // leaves the Audio tab (or the route unmounts) mid-test the mic would stay
  // hot until then. We capture the stream as it's acquired so we can stop it
  // immediately on tab change / unmount. Held in a ref (not state) so cleanup
  // can read the latest value without re-running effects.
  const micStreamRef = useRef<MediaStream | null>(null);

  // Voice Models State
  const [uploadState, setUploadState] = useState<"idle" | "computer" | "chatty">("idle");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = useCallback((field: string, value: string) => {
    navigator.clipboard.writeText(value).then(() => {
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    });
  }, []);

  const { data: devices } = useQuery({
    queryKey: ["audioDevices"],
    queryFn: getAudioDevices,
  });

  const { data: voiceModels, refetch: refetchVoiceModels } = useQuery({
    queryKey: ["voiceModels"],
    queryFn: fetchVoiceModels,
  });

  // Load config on mount
  const { data: remoteConfig, isLoading: configLoading } = useQuery({
    queryKey: ["config"],
    queryFn: loadConfig,
  });
  // Seed the editable form from the remote config during render (not in an
  // effect) so the seed can never land *after* a user edit and clobber it.
  // `seeded` marks the first seed; `lastRemoteJson` remembers the remote payload
  // we last seeded from so we can detect a genuine refetch (React Query returns a
  // fresh object reference on every render with staleTime=0, so identity alone
  // isn't enough).
  const seeded = useRef(false);
  const lastRemoteJson = useRef<string | null>(null);
  if (remoteConfig) {
    const remoteJson = JSON.stringify(remoteConfig);
    if (!seeded.current) {
      // First load: seed both the working copy and the baseline.
      seeded.current = true;
      lastRemoteJson.current = remoteJson;
      setConfig(remoteConfig);
      setBaseline(remoteConfig);
    } else if (remoteJson !== lastRemoteJson.current) {
      // A later refetch returned genuinely different remote data.
      lastRemoteJson.current = remoteJson;
      const isDirty = JSON.stringify(config) !== JSON.stringify(baseline);
      if (!isDirty) {
        // Not dirty: re-seed so we don't show "All changes saved" against stale
        // data. (If dirty, we intentionally leave the in-progress edit alone —
        // see the staleRemote note rendered in the save bar.)
        setConfig(remoteConfig);
        setBaseline(remoteConfig);
      }
    }
  }

  // ─── Dirty-state tracking ──────────────────────────────────────────────────
  // Compare the working config against the loaded/remote baseline.
  const dirty = useMemo(
    () => JSON.stringify(config) !== JSON.stringify(baseline),
    [config, baseline],
  );

  // True when a refetch brought new remote data we couldn't auto-apply because
  // the form has unsaved edits — the baseline is now older than the server.
  const staleRemote = useMemo(
    () =>
      dirty &&
      lastRemoteJson.current !== null &&
      lastRemoteJson.current !== JSON.stringify(baseline),
    [dirty, baseline],
  );

  // Warn on browser-level navigation (reload / close tab) while dirty.
  useEffect(() => {
    if (!dirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
      return "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  // In-app route-leave guard. We don't have a data router (BrowserRouter), so
  // useBlocker isn't available; instead we intercept in-app anchor clicks while
  // dirty and confirm before letting navigation proceed.
  const dirtyRef = useRef(dirty);
  dirtyRef.current = dirty;
  useEffect(() => {
    const onClickCapture = (e: MouseEvent) => {
      if (!dirtyRef.current) return;
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
        return;
      }
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor) return;
      const href = anchor.getAttribute("href") ?? "";
      // Only guard in-app navigations; ignore new tabs / external / hash-only.
      if (!href.startsWith("/") || anchor.target === "_blank") return;
      const ok = window.confirm(
        "You have unsaved configuration changes. Leave this page and discard them?",
      );
      if (!ok) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    document.addEventListener("click", onClickCapture, true);
    return () => document.removeEventListener("click", onClickCapture, true);
  }, []);

  const mutation = useMutation({
    mutationFn: persistConfig,
    onSuccess: (_data, savedConfig) => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
      // The just-saved config is now the clean baseline.
      setBaseline(savedConfig);
      addToast("Configuration saved successfully.", "success");
    },
    onError: (err: unknown) => {
      addToast(
        `Failed to save configuration: ${err instanceof Error ? err.message : "Unknown error"}`,
        "error",
      );
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
      addToast("Voice model uploaded.", "success");
    },
    onError: (err: unknown) => {
      setIsUploading(false);
      setUploadError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteVoiceModel,
    onSuccess: (_data, name) => {
      refetchVoiceModels();
      setPendingDelete(null);
      addToast(`Deleted voice model "${name}".`, "success");
    },
    onError: (err: unknown) => {
      setPendingDelete(null);
      addToast(
        `Failed to delete model: ${err instanceof Error ? err.message : "Please try again."}`,
        "error",
      );
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

  const handleDiscard = useCallback(() => {
    setConfig(baseline);
    // Keep the live theme in sync with the reverted value.
    setTheme(baseline.theme);
    addToast("Reverted unsaved changes.", "info");
  }, [baseline, setTheme, addToast]);

  const handleFetchModels = async () => {
    setFetchingModels(true);
    setModelFetchError(null);
    try {
      const models = await fetchLLMModels(config.llmBaseUrl, config.apiKey || undefined);
      setModelList(models);
      if (models.length === 0) {
        setModelList(["(no models returned — check endpoint/key)"]);
      }
    } catch (err) {
      // A bad URL / key / CORS failure previously surfaced nothing. Tell the
      // user what went wrong instead of silently leaving the list empty.
      const message =
        err instanceof Error && err.message
          ? err.message
          : "Could not fetch models — check the base URL and API key.";
      setModelFetchError(message);
      setModelList([]);
      addToast(`Failed to fetch models: ${message}`, "error");
    } finally {
      setFetchingModels(false);
    }
  };

  // Stop and forget any live mic-test stream. Safe to call repeatedly.
  const stopMicStream = useCallback(() => {
    const stream = micStreamRef.current;
    if (stream) {
      micStreamRef.current = null;
      stream.getTracks().forEach((t) => t.stop());
    }
  }, []);

  const handleTestMic = async () => {
    setMicTestStatus("testing");
    setMicTestError(null);
    setMicLevel(0);
    setMicPeak(0);
    // Capture the MediaStream as runMicTest acquires it (by transiently
    // wrapping getUserMedia) so we hold a handle we can stop early on
    // tab-change/unmount. The wrapper is restored before runMicTest returns.
    const md = navigator.mediaDevices;
    const originalGetUserMedia = md?.getUserMedia?.bind(md);
    if (md && originalGetUserMedia) {
      md.getUserMedia = async (constraints?: MediaStreamConstraints) => {
        const stream = await originalGetUserMedia(constraints);
        micStreamRef.current = stream;
        return stream;
      };
    }
    try {
      const { peakLevel } = await runMicTest({
        durationMs: MIC_TEST_DURATION_MS,
        onLevel: (level) => {
          setMicLevel(level);
          setMicPeak((prev) => Math.max(prev, level));
        },
      });
      setMicLevel(0);
      setMicPeak(peakLevel);
      setMicTestStatus("done");
    } catch (err) {
      setMicLevel(0);
      setMicTestError(
        err instanceof Error && err.message
          ? err.message
          : "Microphone access was denied or is unavailable.",
      );
      setMicTestStatus("error");
    } finally {
      // runMicTest stops its own stream on completion; drop our handle and
      // restore the original getUserMedia.
      micStreamRef.current = null;
      if (md && originalGetUserMedia) {
        md.getUserMedia = originalGetUserMedia;
      }
    }
  };

  const handleTestOutput = async () => {
    setOutputTestStatus("playing");
    setOutputTestError(null);
    try {
      await playTestTone({ durationMs: OUTPUT_TONE_DURATION_MS });
      setOutputTestStatus("done");
    } catch (err) {
      setOutputTestError(
        err instanceof Error && err.message ? err.message : "Could not play the test tone.",
      );
      setOutputTestStatus("error");
    }
  };

  // Stop an in-progress mic test when the user leaves the Audio tab. Note we do
  // NOT depend on micTestStatus here (and use a functional setState) — otherwise
  // starting a test (idle -> testing) would re-run this effect and its cleanup
  // would stop the stream we just opened.
  useEffect(() => {
    if (activeTab !== "audio") {
      stopMicStream();
      setMicTestStatus((s) => (s === "testing" ? "idle" : s));
      setMicLevel((l) => (l !== 0 ? 0 : l));
    }
  }, [activeTab, stopMicStream]);

  // Always release the mic stream on unmount (separate effect so it only fires
  // on unmount, not on every tab/status change).
  useEffect(() => {
    return () => {
      stopMicStream();
    };
  }, [stopMicStream]);

  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: "general", label: "General", icon: <SlidersIcon className="w-4 h-4" /> },
    { id: "audio", label: "Audio", icon: <HeadphonesIcon className="w-4 h-4" /> },
    { id: "models", label: "Voice Models", icon: <FileAudioIcon className="w-4 h-4" /> },
    { id: "llm", label: "LLM", icon: <CpuIcon className="w-4 h-4" /> },
  ];

  // Refs to each tab button so the keyboard handler can move focus along with
  // the active selection (APG tablist roving-tabindex pattern).
  const tabRefs = useRef<Record<TabId, HTMLButtonElement | null>>({
    general: null,
    audio: null,
    models: null,
    llm: null,
  });

  // ARIA Authoring-Practices keyboard nav: Arrow Left/Right move between tabs
  // (wrapping), Home/End jump to the first/last. Activation follows focus.
  const handleTabKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const currentIndex = tabs.findIndex((t) => t.id === activeTab);
    if (currentIndex === -1) return;
    let nextIndex: number | null = null;
    switch (e.key) {
      case "ArrowRight":
      case "ArrowDown":
        nextIndex = (currentIndex + 1) % tabs.length;
        break;
      case "ArrowLeft":
      case "ArrowUp":
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = tabs.length - 1;
        break;
      default:
        return;
    }
    e.preventDefault();
    const nextTab = tabs[nextIndex].id;
    setActiveTab(nextTab);
    // Move focus to the newly-active tab so keyboard navigation is visible.
    tabRefs.current[nextTab]?.focus();
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

      {/* Gate the form on the initial config load so the editable state is
          always seeded before any interaction (prevents a late load from
          clobbering an edit and from showing stale "Saved" state). */}
      {configLoading && !seeded.current ? (
        <div className="card bg-base-100 shadow-xl border border-base-content/10">
          <div className="card-body items-center py-16" data-testid="config-loading">
            <span className="loading loading-spinner loading-lg text-primary" aria-label="Loading configuration"></span>
          </div>
        </div>
      ) : (
      <>

      <div className="card bg-base-100 shadow-xl border border-base-content/10 overflow-visible">
        <div className="card-body p-0">

          {/* Tab navigation. `overflow-x-auto` + `flex-nowrap` keep every tab
              reachable on narrow (phone) widths instead of clipping the last one,
              and the APG roving-tabindex + Arrow/Home/End handler below makes the
              tablist keyboard-navigable. */}
          <div
            role="tablist"
            aria-label="Configuration sections"
            className="tabs tabs-bordered px-4 pt-4 flex-nowrap overflow-x-auto"
            onKeyDown={handleTabKeyDown}
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                ref={(el) => { tabRefs.current[tab.id] = el; }}
                role="tab"
                type="button"
                aria-selected={activeTab === tab.id}
                aria-controls={`config-panel-${tab.id}`}
                id={`config-tab-${tab.id}`}
                tabIndex={activeTab === tab.id ? 0 : -1}
                className={`tab gap-2 ${activeTab === tab.id ? "tab-active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── General ─────────────────────────────────────────────────── */}
          {activeTab === "general" && (
            <div
              role="tabpanel"
              id="config-panel-general"
              aria-labelledby="config-tab-general"
            >
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
                    <select
                      id="config-theme"
                      name="theme"
                      className="select select-bordered w-full"
                      value={config.theme}
                      onChange={handleChange}
                    >
                      {/* Drive options from the themes actually enabled in
                          Tailwind/DaisyUI (AVAILABLE_THEMES) so a pick can never
                          set a non-existent data-theme. If the persisted theme is
                          one that's since been removed, still list it (disabled)
                          so the current value renders honestly rather than blank. */}
                      {!(AVAILABLE_THEMES as readonly string[]).includes(config.theme) && (
                        <option value={config.theme} disabled>
                          {themeLabel(config.theme)} (unavailable)
                        </option>
                      )}
                      {AVAILABLE_THEMES.map((t) => (
                        <option key={t} value={t}>
                          {themeLabel(t)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Services Configuration */}
              <div className="p-6 bg-base-200/50">
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
                        <span className="label-text font-medium text-info flex items-center gap-1">
                          Voice Commands (always-on)
                          <HelpHint
                            label="About always-on voice commands"
                            text="When enabled, the app continuously listens on your microphone for wake-word ONNX models (via openwakeword) — even when no window is focused. Disable to stop background listening."
                          />
                        </span>
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
            </div>
          )}

          {/* ── Audio ───────────────────────────────────────────────────── */}
          {activeTab === "audio" && (
            <div
              role="tabpanel"
              id="config-panel-audio"
              aria-labelledby="config-tab-audio"
            >
              <div className="p-6">
                <h3 className="text-lg font-bold flex items-center gap-2 mb-1">
                  <HeadphonesIcon className="w-5 h-5 text-accent" />
                  Audio Devices
                </h3>
                <p className="text-sm text-base-content/60 mb-4">
                  Device selections below configure the server and are applied on save. The Test
                  buttons run in your browser on its default microphone and speakers.
                </p>

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
                          className="btn btn-sm btn-outline btn-primary"
                          onClick={handleTestMic}
                          disabled={micTestStatus === "testing"}
                          aria-label={micTestStatus === "testing" ? "Testing microphone" : "Test microphone"}
                          data-testid="mic-test-button"
                        >
                          {micTestStatus === "testing" ? "Testing..." : "Test"}
                        </button>
                      </div>

                      <label className="sr-only" htmlFor="audio-input-device">
                        Audio input device
                      </label>
                      <select
                        id="audio-input-device"
                        name="inputDevice"
                        aria-label="Audio input device"
                        className="select select-bordered select-sm w-full select-primary mb-4"
                        value={config.inputDevice}
                        onChange={handleChange}
                      >
                        <option value="" disabled>Select device...</option>
                        {devices?.input.map((dev: string) => (
                          <option key={dev} value={dev}>{dev}</option>
                        ))}
                      </select>

                      {/* Live input level meter / test result */}
                      <div className="h-7 bg-base-200 rounded flex items-center px-2 overflow-hidden">
                        {micTestStatus === "testing" ? (
                          <div
                            role="meter"
                            aria-label="Microphone input level"
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-valuenow={micLevel}
                            data-testid="mic-test-meter"
                            className="w-full h-3 bg-base-300 rounded-full overflow-hidden"
                          >
                            <div
                              className="h-full bg-primary transition-all duration-75"
                              style={{ width: `${micLevel}%` }}
                            />
                          </div>
                        ) : micTestStatus === "done" ? (
                          <span
                            data-testid="mic-test-result"
                            className={`text-xs w-full text-center flex items-center justify-center gap-1 ${micPeak >= MIC_SIGNAL_THRESHOLD ? "text-success" : "text-warning"}`}
                          >
                            {micPeak >= MIC_SIGNAL_THRESHOLD ? (
                              <>
                                <CheckIcon size={12} aria-hidden="true" />
                                {`Signal detected (peak ${micPeak}%)`}
                              </>
                            ) : (
                              <>
                                <AlertTriangleIcon size={12} aria-hidden="true" />
                                No signal detected — check your microphone
                              </>
                            )}
                          </span>
                        ) : micTestStatus === "error" ? (
                          <span data-testid="mic-test-result" className="text-xs text-error w-full text-center flex items-center justify-center gap-1">
                            <AlertTriangleIcon size={12} aria-hidden="true" />
                            {micTestError}
                          </span>
                        ) : (
                          <span className="text-xs text-base-content/50 italic w-full text-center">Click Test</span>
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
                            <VolumeUpIcon size={16} className={outputTestStatus === "playing" ? "animate-bounce" : ""} /> Output Device
                          </h4>
                          <p className="text-xs opacity-70">Playback endpoint</p>
                        </div>
                        <button
                          className="btn btn-sm btn-outline btn-secondary"
                          onClick={handleTestOutput}
                          disabled={outputTestStatus === "playing"}
                          aria-label={outputTestStatus === "playing" ? "Playing test tone" : "Play test tone"}
                          data-testid="output-test-button"
                        >
                          {outputTestStatus === "playing" ? "Playing..." : "Test"}
                        </button>
                      </div>

                      <label className="sr-only" htmlFor="audio-output-device">
                        Audio output device
                      </label>
                      <select
                        id="audio-output-device"
                        name="outputDevice"
                        aria-label="Audio output device"
                        className="select select-bordered select-sm w-full select-secondary mb-4"
                        value={config.outputDevice}
                        onChange={handleChange}
                      >
                        <option value="" disabled>Select device...</option>
                        {devices?.output.map((dev: string) => (
                          <option key={dev} value={dev}>{dev}</option>
                        ))}
                      </select>

                      <div className="h-7 bg-base-200 rounded flex items-center justify-center px-4 overflow-hidden">
                        <span
                          data-testid="output-test-status"
                          className={`text-xs w-full text-center flex items-center justify-center gap-1 ${
                            outputTestStatus === "error"
                              ? "text-error"
                              : outputTestStatus === "done"
                                ? "text-success"
                                : "text-base-content/50 italic"
                          }`}
                        >
                          {outputTestStatus === "playing" && "Playing 440 Hz test tone..."}
                          {outputTestStatus === "done" && (
                            <>
                              <CheckIcon size={12} aria-hidden="true" />
                              Test tone played
                            </>
                          )}
                          {outputTestStatus === "error" && (
                            <>
                              <AlertTriangleIcon size={12} aria-hidden="true" />
                              {outputTestError}
                            </>
                          )}
                          {outputTestStatus === "idle" && "Ready"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Voice Models ────────────────────────────────────────────── */}
          {activeTab === "models" && (
            <div
              role="tabpanel"
              id="config-panel-models"
              aria-labelledby="config-tab-models"
            >
              <div className="p-6">
                <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
                  <FileAudioIcon className="w-5 h-5 text-warning" />
                  Voice Models (ONNX)
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="col-span-2">
                    <div className="overflow-x-auto bg-base-200/30 rounded-lg border border-base-content/5 max-h-60 overflow-y-auto custom-scrollbar">
                      <table className="table table-sm w-full">
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
                                    <span className={`badge badge-sm ${
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
                                    onClick={() => setPendingDelete(model.name)}
                                    title="Delete Model"
                                    aria-label={`Delete model ${model.name}`}
                                    disabled={deleteMutation.isPending}
                                  >
                                    {deleteMutation.isPending && deleteMutation.variables === model.name ? (
                                      <span className="loading loading-spinner loading-xs"></span>
                                    ) : (
                                      <TrashIcon size={14} />
                                    )}
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
                      <UploadIcon size={14} /> Upload Model
                    </h4>

                    <div className="form-control w-full mb-3">
                      <label className="label py-1" htmlFor="upload-target-state">
                        <span className="label-text-alt flex items-center gap-1">
                          Target State
                          <HelpHint
                            label="About wake-word target states"
                            text="Which listening state this wake-word model activates in. Idle = always-on wake word that brings the app to attention. Computer = the active/command state. Chatty = the conversational state."
                          />
                        </span>
                      </label>
                      <select
                        id="upload-target-state"
                        aria-label="Target state for uploaded model"
                        className="select select-bordered select-sm w-full"
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
                        aria-label="Select ONNX voice model file"
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
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── LLM ─────────────────────────────────────────────────────── */}
          {activeTab === "llm" && (
            <div
              role="tabpanel"
              id="config-panel-llm"
              aria-labelledby="config-tab-llm"
            >
              <div className="p-6">
                <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
                  <CpuIcon className="w-5 h-5 text-secondary" />
                  LLM Endpoint
                </h3>
                <div className="space-y-4">
                  <div className="form-control w-full">
                    <label className="label" htmlFor="config-llm-base-url">
                      <span className="label-text font-medium text-base-content flex items-center gap-2">
                        API Base URL
                        <HelpHint
                          label="About the inference framework / base URL"
                          text="OpenAI-compatible base URL of your inference framework (e.g. Ollama, llama.cpp, vLLM, OpenRouter). Must end in the API version path such as /v1. The Model 'Fetch list' button calls this endpoint's /models route."
                        />
                        {config.envOverrides.baseUrl && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                      </span>
                      <span className="label-text-alt text-base-content/40">OpenAI-compatible</span>
                    </label>
                    <div className="flex gap-1 items-center">
                      <input
                        id="config-llm-base-url"
                        type="url"
                        name="llmBaseUrl"
                        placeholder={config.envOverrides.baseUrl ? "(Configured via environment variable)" : "http://localhost:11434/v1"}
                        className="input input-bordered w-full focus:input-secondary disabled:opacity-50"
                        value={config.envOverrides.baseUrl ? "################" : config.llmBaseUrl}
                        onChange={handleChange}
                        disabled={config.envOverrides.baseUrl}
                      />
                      {!config.envOverrides.baseUrl && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-xs"
                          onClick={() => handleCopy("baseUrl", config.llmBaseUrl)}
                          title="Copy to clipboard"
                          aria-label="Copy API Base URL"
                        >
                          {copiedField === "baseUrl" ? <CheckIcon size={14} className="text-success" /> : <CopyIcon size={14} />}
                        </button>
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
                          API Key {config.envOverrides.apiKey && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                        </span>
                      </label>
                      <input
                        id="config-api-key"
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
                      <label className="label" htmlFor="config-model">
                        <span className="label-text font-medium flex items-center gap-2">
                          Model
                          <HelpHint
                            label="About the model field"
                            text="The model identifier sent to the inference framework (e.g. gpt-4o-mini, llama-3.1-8b-instant). Type it directly, or click 'Fetch list' to load the endpoint's available models and pick one."
                          />
                          {config.envOverrides.model && <span className="badge badge-error badge-xs">LOCKED BY ENV</span>}
                        </span>
                        <button
                          type="button"
                          className="btn btn-xs btn-ghost gap-1"
                          onClick={handleFetchModels}
                          disabled={fetchingModels || !config.llmBaseUrl || config.envOverrides.baseUrl || config.envOverrides.model}
                          title="Fetch available models from endpoint"
                        >
                          {fetchingModels ? <span className="loading loading-spinner loading-xs"></span> : <RefreshIcon size={12} />}
                          {fetchingModels ? "Fetching..." : "Fetch list"}
                        </button>
                      </label>
                      {/* Combobox: always allow typing; the fetched list is offered as
                          datalist suggestions so a typed value is never lost when the
                          list loads. */}
                      <div className="flex gap-1 items-center">
                        <input
                          id="config-model"
                          type="text"
                          name="llmModel"
                          list={modelList.length > 0 && !config.envOverrides.model ? "llm-model-options" : undefined}
                          placeholder={config.envOverrides.model ? "(Configured via environment variable)" : "gpt-4o-mini · llama-3.1-8b-instant · …"}
                          className="input input-bordered w-full disabled:opacity-50"
                          value={config.envOverrides.model ? "################" : config.llmModel}
                          onChange={handleChange}
                          disabled={config.envOverrides.model}
                        />
                        {modelList.length > 0 && !config.envOverrides.model && (
                          <datalist id="llm-model-options">
                            {modelList.map((m) => (
                              <option key={m} value={m} />
                            ))}
                          </datalist>
                        )}
                        {!config.envOverrides.model && (
                          <button
                            type="button"
                            className="btn btn-ghost btn-xs"
                            onClick={() => handleCopy("model", config.llmModel)}
                            title="Copy to clipboard"
                            aria-label="Copy Model"
                          >
                            {copiedField === "model" ? <CheckIcon size={14} className="text-success" /> : <CopyIcon size={14} />}
                          </button>
                        )}
                      </div>
                      {modelFetchError && (
                        <label className="label">
                          <span
                            data-testid="model-fetch-error"
                            className="label-text-alt text-error flex items-center gap-1"
                          >
                            <AlertTriangleIcon size={12} aria-hidden="true" />
                            {modelFetchError}
                          </span>
                        </label>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Sticky Save Bar ─────────────────────────────────────────── */}
          <div className="sticky bottom-0 z-20 p-4 bg-base-300/90 backdrop-blur rounded-b-xl border-t border-base-content/10 flex flex-wrap justify-between items-center gap-3">
            <span
              data-testid="dirty-status"
              className={`text-sm flex items-center gap-1 ${dirty ? "text-warning" : "text-base-content/60"}`}
            >
              {dirty ? (
                <>
                  <AlertTriangleIcon size={14} aria-hidden="true" />
                  Unsaved changes
                </>
              ) : (
                <>
                  <CheckIcon size={14} aria-hidden="true" />
                  All changes saved
                </>
              )}
            </span>
            {staleRemote && (
              <span
                data-testid="stale-remote-note"
                className="text-xs text-info flex items-center gap-1"
              >
                <AlertTriangleIcon size={12} aria-hidden="true" />
                Settings changed on the server since you started editing — saving will overwrite them.
              </span>
            )}
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="btn btn-ghost gap-2"
                onClick={handleDiscard}
                disabled={!dirty || mutation.isPending}
                data-testid="discard-button"
              >
                <RotateCcwIcon size={16} />
                Discard changes
              </button>
              <button
                className="btn btn-primary gap-2"
                onClick={() => mutation.mutate(config)}
                disabled={mutation.isPending || !dirty}
                data-testid="save-button"
              >
                {mutation.isPending ? <span className="loading loading-spinner"></span> : <SaveIcon size={20} />}
                {mutation.isPending ? "Saving..." : dirty ? "Save Changes" : "Saved"}
              </button>
            </div>
          </div>

        </div>
      </div>

      {/* ── Delete-confirm dialog ───────────────────────────────────────── */}
      {pendingDelete && (
        <div className="modal modal-open" role="dialog" aria-modal="true" aria-labelledby="delete-model-title">
          <div className="modal-box">
            <h3 id="delete-model-title" className="font-bold text-lg flex items-center gap-2 text-error">
              <AlertTriangleIcon size={20} aria-hidden="true" />
              Delete voice model?
            </h3>
            <p className="py-4 text-sm">
              This permanently removes the wake-word model{" "}
              <span className="font-mono font-semibold">{pendingDelete}</span> from the server.
              This cannot be undone.
            </p>
            <div className="modal-action">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setPendingDelete(null)}
                data-testid="delete-cancel"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-error gap-2"
                onClick={() => deleteMutation.mutate(pendingDelete)}
                disabled={deleteMutation.isPending}
                data-testid="delete-confirm"
              >
                {deleteMutation.isPending ? (
                  <span className="loading loading-spinner loading-xs"></span>
                ) : (
                  <TrashIcon size={16} />
                )}
                Delete
              </button>
            </div>
          </div>
          <button
            type="button"
            className="modal-backdrop"
            aria-label="Close dialog"
            onClick={() => setPendingDelete(null)}
          />
        </div>
      )}
      </>
      )}
    </div>
  );
};

export default ConfigurationPage;
