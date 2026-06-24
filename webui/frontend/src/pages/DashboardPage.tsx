import React, { useState, useEffect, useCallback, useMemo, useRef, Suspense, lazy } from "react";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Server, Clock, Terminal, Wifi, WifiOff, Send, Activity as AssessmentIcon, Pause, Play, Download, Zap, Mic, X } from "lucide-react";
import { apiService } from "../services/apiService";
import { fetchAgentStatus, Agent } from "../services/api";
import { formatTimestamp } from "../utils/formatTime";
import DograhStatusCard from "../components/DograhStatusCard";
import CallStateBadge, { DograhCallStatePayload } from "../components/CallStateBadge";
import type { PerfMetric } from "../components/PerformanceChart";

// Lazy-load the recharts-backed chart so the heavy charting bundle is split out
// of the main DashboardPage chunk and only fetched when the dashboard renders.
const PerformanceChart = lazy(() => import("../components/PerformanceChart"));

const MAX_MESSAGES = 100;
const MAX_RECENT_MESSAGES = 15;
const MAX_HISTORY_ITEMS = 20;

// Telemetry arrives roughly every 5s; treat the WS as "stale" once we've gone
// more than ~2 intervals without any frame, even if it's technically connected.
const TELEMETRY_INTERVAL_SECONDS = 5;
const STALE_THRESHOLD_SECONDS = TELEMETRY_INTERVAL_SECONDS * 2;

const DashboardPage = React.memo(() => {
  useEffect(() => {
    document.title = "Dashboard | ChattyCommander";
  }, []);

  const { ws, isConnected, reconnectAttempt, lastMessageTime } = useWebSocket();
  const isReconnecting = !isConnected && reconnectAttempt > 0;
  // Log entries carry a monotonic id (a counter) alongside their text so rows
  // can be keyed stably even as the ring buffer scrolls and timestamps repeat.
  const [messages, setMessages] = useState<{ id: number; text: string }[]>([]);
  const msgCounter = useRef(0);
  const appendMessage = useCallback((text: string) => {
    setMessages((prev) => {
      const entry = { id: msgCounter.current++, text };
      return prev.length >= MAX_MESSAGES ? [...prev.slice(1), entry] : [...prev, entry];
    });
  }, []);
  const [lastMsgAgo, setLastMsgAgo] = useState<string>("No messages yet");
  const [lastMsgSeconds, setLastMsgSeconds] = useState<number | null>(null);

  // Update "last message ago" display every second
  useEffect(() => {
    if (!lastMessageTime) {
      setLastMsgSeconds(null);
      return;
    }
    const update = () => {
      const seconds = Math.round((Date.now() - lastMessageTime) / 1000);
      setLastMsgSeconds(seconds);
      if (seconds < 60) {
        setLastMsgAgo(`${seconds}s ago`);
      } else {
        const minutes = Math.floor(seconds / 60);
        setLastMsgAgo(`${minutes}m ${seconds % 60}s ago`);
      }
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [lastMessageTime]);

  // A connected socket whose last frame is older than the staleness threshold is
  // "stale" — surfaced as a warning so a green card doesn't mislead.
  const isStale =
    isConnected && lastMsgSeconds !== null && lastMsgSeconds > STALE_THRESHOLD_SECONDS;

  // Memoize the recent messages slice to avoid inline allocation during frequent re-renders.
  const recentMessages = useMemo(() => {
    return messages.length > MAX_RECENT_MESSAGES ? messages.slice(-MAX_RECENT_MESSAGES) : messages;
  }, [messages]);

  const [commandInput, setCommandInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [history, setHistory] = useState<PerfMetric[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [welcomeDismissed, setWelcomeDismissed] = useState(false);

  // Current state-machine mode (idle/computer/chatty). Seeded from
  // GET /api/v1/status and then driven live by the `state_change` WS frame.
  // Mic-active is not currently surfaced by the backend, so we show it as
  // "unknown" rather than inventing a value.
  const [currentMode, setCurrentMode] = useState<string | null>(null);

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    setIsSending(true);
    const cmd = commandInput;
    setCommandInput("");

    // Optimistically add to log
    const ts = formatTimestamp(new Date());
    appendMessage(`[${ts}] > Executing: ${cmd}`);

    try {
      await apiService.executeCommand(cmd);
    } catch (err: any) {
      const errTs = formatTimestamp(new Date());
      appendMessage(`[${errTs}] Error: ${err.message}`);
    } finally {
      setIsSending(false);
    }
  };

  const { data: initialSystemStatus, isLoading } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: async () => {
      const res = await fetch("/health");
      if (!res.ok) return { status: "Unknown", uptime: "N/A", commandsExecuted: 0, cpu: "N/A", memory: "N/A" };
      const data = await res.json();
      return {
        status: data.status === "healthy" ? "Healthy" : data.status ?? "Unknown",
        uptime: data.uptime ?? "N/A",
        commandsExecuted: data.commands_executed ?? 0,
        version: data.version,
        cpu: data.cpu_usage ?? "N/A",
        memory: data.memory_usage ?? "N/A",
      };
    },
    refetchInterval: 5000,
  });

  const [realtimeStatus, setRealtimeStatus] = useState<{ cpu?: string; memory?: string } | null>(null);
  const systemStatus = useMemo(() => ({ ...initialSystemStatus, ...realtimeStatus }), [initialSystemStatus, realtimeStatus]);

  // Live Dograh call state. Seed from the cached snapshot on mount so the badge
  // reflects the last known state before any WS frame arrives, then let the
  // 'dograh_call_state' WS message drive subsequent updates.
  const [callState, setCallState] = useState<DograhCallStatePayload | null>(null);
  const { data: seededCallState } = useQuery<DograhCallStatePayload | null>({
    queryKey: ["dograh", "callState"],
    queryFn: async () => {
      const res = await fetch("/api/v1/dograh/call-state");
      if (!res.ok) return null;
      return (await res.json()) as DograhCallStatePayload;
    },
    retry: false,
  });
  useEffect(() => {
    // Only seed while we have not yet received a live WS frame.
    if (seededCallState) {
      setCallState((prev) => prev ?? seededCallState);
    }
  }, [seededCallState]);

  // Seed the current state-machine mode from the status endpoint so the Voice
  // card reflects the last known mode before any `state_change` WS frame.
  const { data: seededStatus } = useQuery<{ current_state?: string } | null>({
    queryKey: ["systemStatusState"],
    queryFn: async () => {
      const res = await fetch("/api/v1/status");
      if (!res.ok) return null;
      return (await res.json()) as { current_state?: string };
    },
    retry: false,
  });
  useEffect(() => {
    if (seededStatus?.current_state) {
      setCurrentMode((prev) => prev ?? seededStatus.current_state ?? null);
    }
  }, [seededStatus]);

  // Update history chart from telemetry
  useEffect(() => {
    if (systemStatus && !isPaused) {
      const cpuStr = String(systemStatus.cpu).replace("%", "");
      const memStr = String(systemStatus.memory).replace("%", "");
      const cpuVal = parseFloat(cpuStr) || 0;
      const memVal = parseFloat(memStr) || 0;
      const now = new Date().toLocaleTimeString();

      // Performance optimization: prevent unnecessary intermediate array allocation
      // by slicing `prev` conditionally before creating the new array.
      setHistory(prev => {
        const item = { time: now, cpu: cpuVal, memory: memVal };
        return prev.length >= MAX_HISTORY_ITEMS ? [...prev.slice(1), item] : [...prev, item];
      });
    }
  }, [systemStatus, isPaused]);

  const handleExport = () => {
    const headers = "Time,CPU,Memory\n";
    const csvContent = "data:text/csv;charset=utf-8,"
      + headers
      + history.map(row => `${row.time},${row.cpu},${row.memory}`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "performance_history.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const { data: agentData, isLoading: agentsLoading, isError: agentsError, error: agentsErrObj } = useQuery<Agent[]>({
    queryKey: ["agentStatus"],
    queryFn: fetchAgentStatus,
    refetchInterval: 30000,
    retry: 2,
  });

  const getAgentStatusColor = (status: Agent["status"]) => {
    switch (status) {
      case "online": return "badge-success";
      case "offline": return "badge-ghost";
      case "error": return "badge-error";
      case "processing": return "badge-warning";
      default: return "badge-ghost";
    }
  };

  const handleWsMessage = useCallback((event: MessageEvent) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "telemetry" && msg.data) {
        setRealtimeStatus((prev: { cpu?: string; memory?: string } | null) => ({
          ...prev,
          cpu: msg.data.cpu !== undefined ? `${Number(msg.data.cpu).toFixed(1)}` : prev?.cpu,
          memory: msg.data.memory !== undefined ? `${Number(msg.data.memory).toFixed(1)}` : prev?.memory,
        }));
        return;
      }
      if (msg.type === "state_change" && msg.data) {
        const next = msg.data.new_state ?? msg.data.current_state;
        if (typeof next === "string") {
          setCurrentMode(next);
        }
        return;
      }
      if (msg.type === "dograh_call_state" && msg.data) {
        setCallState({
          state: msg.data.state ?? "unknown",
          workflow_id: msg.data.workflow_id ?? null,
          run_id: msg.data.run_id ?? null,
        });
        return;
      }
      // Fallback for non-JSON or other messages
      if (msg.data && typeof msg.data === "string") {
        const wsTs = formatTimestamp(new Date());
        appendMessage(`[${wsTs}] ${msg.data as string}`);
      }
    } catch {
      // Plain text message
      const wsTs = formatTimestamp(new Date());
      appendMessage(`[${wsTs}] ${event.data as string}`);
    }
  }, [appendMessage]); // setRealtimeStatus is stable; appendMessage is memoized

  useEffect(() => {
    if (!ws) return;
    // Use addEventListener to avoid overwriting other handlers
    ws.addEventListener("message", handleWsMessage);
    return () => {
      ws.removeEventListener("message", handleWsMessage);
    };
  }, [ws, handleWsMessage]);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading dashboard">
        <div className="h-10 w-48 skeleton rounded-lg"></div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="stats shadow bg-base-100 border border-base-content/10 h-28 skeleton rounded-box"></div>
          ))}
        </div>

        <div className="card bg-base-100 shadow-xl border border-base-content/10 h-80 skeleton rounded-box"></div>

        <div className="card bg-base-100 shadow-xl border border-base-content/10 h-96 skeleton rounded-box"></div>

        <div className="h-8 w-48 skeleton mt-8 mb-4 rounded-lg"></div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card bg-base-100 shadow-xl border border-base-content/10 h-48 skeleton rounded-box"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          Dashboard
        </h2>
        {/* Header-level freshness indicator. */}
        <div
          className={`flex items-center gap-1.5 text-xs font-medium ${
            !isConnected ? "text-error" : isStale ? "text-warning" : "text-success"
          }`}
          aria-live="polite"
          data-testid="freshness-indicator"
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              !isConnected
                ? "bg-error"
                : isStale
                  ? "bg-warning"
                  : "bg-success animate-pulse"
            }`}
            aria-hidden="true"
          />
          <span>
            {!isConnected
              ? "offline"
              : isStale
                ? `stale · updated ${lastMsgAgo}`
                : lastMsgSeconds !== null
                  ? `live · updated ${lastMsgAgo}`
                  : "live"}
          </span>
        </div>
      </div>

      {/* Dismissible welcome hero — compact so it doesn't push telemetry below the fold. */}
      {!welcomeDismissed && (
        <div className="alert bg-base-200 border border-base-content/10 py-2" role="status">
          <Mic size={18} className="text-primary" aria-hidden="true" />
          <span className="text-sm">
            Welcome to ChattyCommander — your voice assistant control center. Monitor status, watch the live log, and run commands below.
          </span>
          <button
            type="button"
            className="btn btn-ghost btn-xs btn-square"
            onClick={() => setWelcomeDismissed(true)}
            aria-label="Dismiss welcome message"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

        {/* Voice / Listening — "is my voice assistant working right now?" */}
        <div
          className="stats shadow bg-base-100 border border-primary/30"
          data-testid="voice-status-card"
          data-voice-mode={currentMode ?? "unknown"}
        >
          <div className="stat">
            <div className="stat-figure text-primary">
              <Mic size={32} />
            </div>
            <div className="stat-title">Voice Assistant</div>
            <div className="stat-value text-primary text-2xl capitalize">
              {currentMode ?? "unknown"}
            </div>
            <div className="stat-desc">
              {/* Mic-active state is not reported by the backend; show it honestly. */}
              Mic: <span className="font-medium">unknown</span> · current mode
            </div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-primary" aria-hidden="true">
              <Server size={32} aria-hidden="true" />
            </div>
            <div className="stat-title">System Status</div>
            <div className="stat-value text-primary">{systemStatus?.status || "Unknown"}</div>
            <div className="stat-desc">Core services running</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-secondary">
              <Clock size={32} />
            </div>
            <div className="stat-title">Uptime</div>
            <div className="stat-value text-secondary text-2xl">{systemStatus?.uptime || "N/A"}</div>
            <div className="stat-desc">Since last restart</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-accent">
              <Terminal size={32} />
            </div>
            <div className="stat-title">Commands</div>
            <div className="stat-value text-accent">{systemStatus?.commandsExecuted || 0}</div>
            <div className="stat-desc">Total executed</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-info">
              <div
                className="radial-progress text-info"
                style={{ "--value": Math.round(parseFloat(systemStatus?.cpu || "0")) } as React.CSSProperties}
                role="progressbar"
                aria-label="CPU load"
                aria-valuenow={Math.round(parseFloat(systemStatus?.cpu || "0"))}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                {Math.round(parseFloat(systemStatus?.cpu || "0"))}%
              </div>
            </div>
            <div className="stat-title">CPU Load</div>
            <div className="stat-value text-info text-2xl">
              {systemStatus?.cpu != null && systemStatus?.cpu !== "N/A"
                ? `${Math.round(parseFloat(systemStatus.cpu))}%`
                : "N/A"}
            </div>
            <div className="stat-desc">Processor usage</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-warning">
              <div
                className="radial-progress text-warning"
                style={{ "--value": Math.round(parseFloat(systemStatus?.memory || "0")) } as React.CSSProperties}
                role="progressbar"
                aria-label="Memory usage"
                aria-valuenow={Math.round(parseFloat(systemStatus?.memory || "0"))}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                {Math.round(parseFloat(systemStatus?.memory || "0"))}%
              </div>
            </div>
            <div className="stat-title">Memory</div>
            <div className="stat-value text-warning text-2xl">
              {systemStatus?.memory != null && systemStatus?.memory !== "N/A"
                ? `${Math.round(parseFloat(systemStatus.memory))}%`
                : "N/A"}
            </div>
            <div className="stat-desc">RAM usage</div>
          </div>
        </div>

        <div
          className={`stats shadow bg-base-100 border ${isStale ? "border-warning/40" : "border-base-content/10"}`}
          data-testid="websocket-card"
          data-ws-state={!isConnected ? (isReconnecting ? "reconnecting" : "offline") : isStale ? "stale" : "connected"}
        >
          <div className="stat">
            <div className="stat-figure">
              {isConnected ?
                (isStale ?
                  <Wifi size={32} className="text-warning" /> :
                  <Wifi size={32} className="text-success" />) :
                isReconnecting ?
                  <Wifi size={32} className="text-warning animate-pulse" /> :
                  <WifiOff size={32} className="text-error" />
              }
            </div>
            <div className="stat-title">WebSocket</div>
            <div className={`stat-value text-2xl ${isConnected ? (isStale ? 'text-warning' : 'text-success') : isReconnecting ? 'text-warning animate-pulse' : 'text-error'}`}>
              {isConnected ? (isStale ? "Stale" : "Connected") : isReconnecting ? `Reconnecting... (attempt ${reconnectAttempt})` : "Offline"}
            </div>
            <div className="stat-desc flex items-center gap-1">
              <Zap size={14} className={isStale ? "text-warning" : "text-accent"} />
              <span>
                {isStale ? "No data — last msg: " : "Last msg: "}
                {lastMsgAgo}
              </span>
            </div>
          </div>
        </div>

        <DograhStatusCard />

        <CallStateBadge call={callState} />
      </div>

      {/* Real-time Performance History Chart */}
      <div className="card bg-base-100 shadow-xl border border-base-content/10">
        <div className="card-body">
          <div className="flex justify-between items-center mb-4">
            <h3 className="card-title text-xl">Real-time Performance History</h3>
            <div className="flex gap-2">
              <div className="tooltip" data-tip={isPaused ? "Resume" : "Pause"}>
                <button
                  className="btn btn-sm btn-ghost btn-square"
                  onClick={() => setIsPaused(!isPaused)}
                  aria-label={isPaused ? "Resume Chart" : "Pause Chart"}
                >
                  {isPaused ? <Play size={18} /> : <Pause size={18} />}
                </button>
              </div>
              <div className="tooltip" data-tip="Export CSV">
                <button
                  className="btn btn-sm btn-ghost btn-square"
                  onClick={handleExport}
                  aria-label="Export Data as CSV"
                >
                  <Download size={18} />
                </button>
              </div>
            </div>
          </div>
          <div className="h-64 w-full">
            <Suspense
              fallback={
                <div
                  className="h-full w-full skeleton rounded-box flex items-center justify-center"
                  aria-busy="true"
                  aria-label="Loading performance chart"
                >
                  <span className="loading loading-spinner text-primary"></span>
                </div>
              }
            >
              <PerformanceChart history={history} />
            </Suspense>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="card bg-base-100 shadow-xl border border-base-content/10">
        <div className="card-body">
          <h3 className="card-title text-xl mb-4">Real-time Command Log</h3>

          <div
            role="log"
            aria-live="polite"
            aria-label="Real-time command log"
            className="bg-base-300 rounded-box h-[20rem] overflow-y-auto w-full custom-scrollbar p-4 font-mono text-xs space-y-1"
          >
            {recentMessages.length > 0 ? (
              recentMessages.map((msg) => (
                // Key on the stable monotonic id rather than the array index,
                // which shifts as the ring buffer scrolls.
                <div key={msg.id} className="text-base-content/80 leading-relaxed">{msg.text}</div>
              ))
            ) : (
              <div className="p-4 text-base-content/50 italic text-center pt-24">
                Waiting for commands...
              </div>
            )}
          </div>

          {/* Command execution is a REST call, so it works even when the WS
              live feed is down — only disable while a request is in flight. */}
          <form onSubmit={handleSendCommand} className="mt-4 flex gap-2">
            <input
              type="text"
              placeholder="Type a command to execute..."
              aria-label="Type and execute a command"
              className="input input-bordered w-full focus:input-primary"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              disabled={isSending}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!commandInput.trim() || isSending}
            >
              {isSending ? <span className="loading loading-spinner"></span> : <Send size={18} />}
              Execute
            </button>
          </form>
          {!isConnected && (
            <p className="mt-2 text-xs text-base-content/60">
              Live updates are offline, but commands still run via the API.
            </p>
          )}
        </div>
      </div>

      {/* Agent Status Section */}
      <h3 className="text-2xl font-bold bg-gradient-to-r from-error to-warning bg-clip-text text-transparent mt-8 mb-4 flex items-center gap-2">
        <AssessmentIcon size={24} className="text-error" /> Agent Status
      </h3>

      {agentsError && (
        <div className="alert alert-error shadow-lg" role="alert">
          <span>{(agentsErrObj as Error)?.message || "Failed to fetch agent status."}</span>
        </div>
      )}

      {agentsLoading ? (
        <div className="flex justify-center p-8">
          <span className="loading loading-spinner text-primary"></span>
        </div>
      ) : agentData?.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10" role="status" aria-label="No agents configured">
          <AssessmentIcon size={48} className="text-base-content/20 mb-4" />
          <h3 className="text-lg font-semibold text-base-content/70">No agents configured</h3>
          <p className="text-base-content/50 mt-2 max-w-md text-center">
            Advisors and agents will appear here once they are configured and connect to the system.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agentData?.map((agent) => (
            <div key={agent.id} className="card bg-base-100 shadow-xl border border-base-content/10">
              <div className="card-body p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="card-title text-xl font-bold">{agent.name}</h3>
                  <div className={`badge ${getAgentStatusColor(agent.status)} badge-lg font-bold uppercase`}>
                    {agent.status}
                  </div>
                </div>

                {agent.error && (
                  <div className="alert alert-error shadow-sm text-xs py-2 my-2 rounded-lg" role="alert">
                    <span>{agent.error}</span>
                  </div>
                )}

                <div className="mockup-code bg-base-300 text-xs mt-2 before:hidden p-0">
                  <div className="px-4 py-3 space-y-3">
                    <div className="flex flex-col">
                      <span className="text-base-content/50 uppercase text-[10px] tracking-wider font-bold">Last Sent</span>
                      <span className="font-mono text-primary">{agent.lastMessageSent || "-"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-base-content/50 uppercase text-[10px] tracking-wider font-bold">Last Received</span>
                      <span className="font-mono text-secondary">{agent.lastMessageReceived || "-"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-base-content/50 uppercase text-[10px] tracking-wider font-bold">Content</span>
                      <span className="font-mono text-base-content/70 break-words mt-1">{agent.lastMessageContent || "-"}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

export default DashboardPage;
