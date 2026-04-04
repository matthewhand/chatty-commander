import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Server, Clock, Terminal, Wifi, WifiOff, Send, Activity as AssessmentIcon, Pause, Play, Download, Zap } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { apiService } from "../services/apiService";
import { fetchAgentStatus, Agent } from "../services/api";
import { formatTimestamp } from "../utils/formatTime";
import {
  Button,
  Card,
  Alert,
  Badge,
  Input,
  LoadingSpinner,
  Skeleton,
  SkeletonStatsCards,
  StatsCard,
} from "../components/DaisyUI";
import TooltipWrapper from "../components/DaisyUI/Tooltip";

const MAX_MESSAGES = 100;
const MAX_RECENT_MESSAGES = 15;
const MAX_HISTORY_ITEMS = 20;

interface PerfMetric {
  time: string;
  cpu: number;
  memory: number;
}

interface CommandMessage {
  content: string;
  isCommand: boolean;
  source: string;
  timestamp: Date;
  isError?: boolean;
}

const CustomTooltip = React.memo(({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-base-300 border border-base-content/20 p-3 rounded-lg shadow-xl text-xs">
        <p className="font-mono mb-2 text-base-content/60">{label}</p>
        {payload.map((entry: any) => (
          <div key={entry.name} className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.stroke }} />
            <span className="font-semibold" style={{ color: entry.stroke }}>
              {entry.name}: {entry.value.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
});

const DashboardPage = React.memo(() => {
  useEffect(() => {
    document.title = "Dashboard | ChattyCommander";
  }, []);

  const { ws, isConnected, reconnectAttempt, lastMessageTime } = useWebSocket();
  const isReconnecting = !isConnected && reconnectAttempt > 0;
  const [messages, setMessages] = useState<CommandMessage[]>([]);
  const [lastMsgAgo, setLastMsgAgo] = useState<string>("No messages yet");

  // Update "last message ago" display every second
  useEffect(() => {
    if (!lastMessageTime) return;
    const update = () => {
      const seconds = Math.round((Date.now() - lastMessageTime) / 1000);
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

  // Performance optimization: Memoize the recent messages derived array
  // to avoid inline `messages.slice(-15)` during frequent real-time re-renders.
  const recentMessages = useMemo(() => {
    return messages.length > MAX_RECENT_MESSAGES ? messages.slice(-MAX_RECENT_MESSAGES) : messages;
  }, [messages]);

  const [commandInput, setCommandInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [history, setHistory] = useState<PerfMetric[]>([]);
  const [isPaused, setIsPaused] = useState(false);

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    setIsSending(true);
    const cmd = commandInput;
    setCommandInput("");

    // Optimistically add to log
    const ts = new Date();
    setMessages((prev) => {
      const msg: CommandMessage = { content: `Executing: ${cmd}`, isCommand: true, source: "You", timestamp: ts };
      return prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg];
    });

    try {
      await apiService.executeCommand(cmd);
    } catch (err: any) {
      const errTs = new Date();
      setMessages((prev) => {
        const msg: CommandMessage = { content: `Error: ${err.message}`, isCommand: false, source: "System", timestamp: errTs, isError: true };
        return prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg];
      });
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

  const [realtimeStatus, setRealtimeStatus] = useState<any>(null);
  const systemStatus = useMemo(() => ({ ...initialSystemStatus, ...realtimeStatus }), [initialSystemStatus, realtimeStatus]);

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

  const getAgentStatusColor = useCallback((status: Agent["status"]): "success" | "ghost" | "error" | "warning" => {
    switch (status) {
      case "online": return "success";
      case "offline": return "ghost";
      case "error": return "error";
      case "processing": return "warning";
      default: return "ghost";
    }
  }, []);

  const agentCards = useMemo(() => agentData?.map((agent) => (
    <Card key={agent.id} className="shadow-xl border border-base-content/10">
      <div className="card-body p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="card-title text-xl font-bold">{agent.name}</h3>
          <Badge variant={getAgentStatusColor(agent.status)} size="large" className="font-bold uppercase">
            {agent.status}
          </Badge>
        </div>

        {agent.error && (
          <Alert variant="error" className="shadow-sm text-xs py-2 my-2 rounded-lg">
            <span>{agent.error}</span>
          </Alert>
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
    </Card>
  )), [agentData, getAgentStatusColor]);

  const handleWsMessage = useCallback((event: MessageEvent) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "telemetry" && msg.data) {
        setRealtimeStatus((prev: any) => ({
          ...prev,
          cpu: msg.data.cpu !== undefined ? `${Number(msg.data.cpu).toFixed(1)}` : prev?.cpu,
          memory: msg.data.memory !== undefined ? `${Number(msg.data.memory).toFixed(1)}` : prev?.memory,
        }));
        return;
      }
      // Fallback for non-JSON or other messages
      if (msg.data && typeof msg.data === "string") {
        const wsTs = new Date();
        setMessages((prev) => {
          const entry: CommandMessage = { content: msg.data as string, isCommand: false, source: "Server", timestamp: wsTs };
          return prev.length >= MAX_MESSAGES ? [...prev.slice(1), entry] : [...prev, entry];
        });
      }
    } catch {
      // Plain text message
      const wsTs = new Date();
      setMessages((prev) => {
        const entry: CommandMessage = { content: event.data as string, isCommand: false, source: "Server", timestamp: wsTs };
        return prev.length >= MAX_MESSAGES ? [...prev.slice(1), entry] : [...prev, entry];
      });
    }
  }, []); // setRealtimeStatus and setMessages are stable; no external deps

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
        <Skeleton width="12rem" height="2.5rem" className="rounded-lg" />

        <SkeletonStatsCards count={6} className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3" />

        <Skeleton width="100%" height="20rem" className="rounded-box" />

        <Skeleton width="100%" height="24rem" className="rounded-box" />

        <Skeleton width="12rem" height="2rem" className="mt-8 mb-4 rounded-lg" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} width="100%" height="12rem" className="rounded-box" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
        Dashboard
      </h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

        <StatsCard
          title="System Status"
          value={systemStatus?.status || "Unknown"}
          description="Core services running"
          icon={<Server size={32} />}
          color="text-primary"
        />

        <StatsCard
          title="Uptime"
          value={systemStatus?.uptime || "N/A"}
          description="Since last restart"
          icon={<Clock size={32} />}
          color="text-secondary"
          className=""
        />

        <StatsCard
          title="Commands"
          value={systemStatus?.commandsExecuted || 0}
          description="Total executed"
          icon={<Terminal size={32} />}
          color="text-accent"
        />

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-info">
              <div className="radial-progress text-info" style={{ "--value": parseFloat(systemStatus?.cpu || "0") } as any} role="progressbar">{parseInt(systemStatus?.cpu || "0")}%</div>
            </div>
            <div className="stat-title">CPU Load</div>
            <div className="stat-value text-info text-2xl">{systemStatus?.cpu || "N/A"}</div>
            <div className="stat-desc">Processor usage</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-warning">
              <div className="radial-progress text-warning" style={{ "--value": parseFloat(systemStatus?.memory || "0") } as any} role="progressbar">{parseInt(systemStatus?.memory || "0")}%</div>
            </div>
            <div className="stat-title">Memory</div>
            <div className="stat-value text-warning text-2xl">{systemStatus?.memory || "N/A"}</div>
            <div className="stat-desc">RAM usage</div>
          </div>
        </div>

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure">
              {isConnected ?
                <Wifi size={32} className="text-success" /> :
                isReconnecting ?
                  <Wifi size={32} className="text-warning animate-pulse" /> :
                  <WifiOff size={32} className="text-error" />
              }
            </div>
            <div className="stat-title">WebSocket</div>
            <div className={`stat-value text-2xl ${isConnected ? 'text-success' : isReconnecting ? 'text-warning animate-pulse' : 'text-error'}`}>
              {isConnected ? "Connected" : isReconnecting ? `Reconnecting... (attempt ${reconnectAttempt})` : "Offline"}
            </div>
            <div className="stat-desc flex items-center gap-1">
              <Zap size={14} className="text-accent" />
              <span>Last msg: {lastMsgAgo}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Performance History Chart */}
      <Card className="shadow-xl border border-base-content/10">
        <div className="card-body">
          <div className="flex justify-between items-center mb-4">
            <h3 className="card-title text-xl">Real-time Performance History</h3>
            <div className="flex gap-2">
              <TooltipWrapper content={isPaused ? "Resume" : "Pause"}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="btn-square"
                  onClick={() => setIsPaused(!isPaused)}
                  aria-label={isPaused ? "Resume Chart" : "Pause Chart"}
                >
                  {isPaused ? <Play size={18} /> : <Pause size={18} />}
                </Button>
              </TooltipWrapper>
              <TooltipWrapper content="Export CSV">
                <Button
                  variant="ghost"
                  size="sm"
                  className="btn-square"
                  onClick={handleExport}
                  aria-label="Export Data as CSV"
                >
                  <Download size={18} />
                </Button>
              </TooltipWrapper>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3abff8" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3abff8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#fbbd23" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#fbbd23" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="time" hide />
                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3abff8"
                  fillOpacity={1}
                  fill="url(#colorCpu)"
                  name="CPU"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke="#fbbd23"
                  fillOpacity={1}
                  fill="url(#colorMem)"
                  name="Memory"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </Card>

      {/* Main Content - Command Log with Chat Bubbles */}
      <Card className="shadow-xl border border-base-content/10">
        <div className="card-body">
          <h3 className="card-title text-xl mb-4">Real-time Command Log</h3>

          <div className="bg-base-300 rounded-box h-[20rem] overflow-y-auto w-full custom-scrollbar p-4">
            {recentMessages.length > 0 ? (
              recentMessages.map((msg, index) => (
                <div key={index} className={`chat ${msg.isCommand ? 'chat-end' : 'chat-start'}`}>
                  <div className="chat-header">{msg.source || 'System'}</div>
                  <div className={`chat-bubble ${msg.isCommand ? 'chat-bubble-primary' : msg.isError ? 'chat-bubble-error' : 'chat-bubble-secondary'}`}>
                    {msg.content}
                  </div>
                  <div className="chat-footer opacity-50">{formatTimestamp(msg.timestamp)}</div>
                </div>
              ))
            ) : (
              <div className="p-4 text-base-content/50 italic text-center pt-24">
                Waiting for commands...
              </div>
            )}
          </div>

          <form onSubmit={handleSendCommand} className="mt-4 flex gap-2">
            <Input
              type="text"
              placeholder="Type a command to execute..."
              aria-label="Type and execute a command"
              variant="primary"
              className="w-full"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              disabled={isSending || !isConnected}
            />
            <Button
              type="submit"
              variant="primary"
              disabled={!commandInput.trim() || isSending || !isConnected}
              loading={isSending}
              icon={!isSending ? <Send size={18} /> : undefined}
            >
              Execute
            </Button>
          </form>
        </div>
      </Card>

      {/* Agent Status Section */}
      <h3 className="text-2xl font-bold bg-gradient-to-r from-error to-warning bg-clip-text text-transparent mt-8 mb-4 flex items-center gap-2">
        <AssessmentIcon size={24} className="text-error" /> Agent Status
      </h3>

      {agentsError && (
        <Alert variant="error" className="shadow-lg">
          <span>{(agentsErrObj as Error)?.message || "Failed to fetch agent status."}</span>
        </Alert>
      )}

      {agentsLoading ? (
        <div className="flex justify-center p-8">
          <LoadingSpinner size="md" color="primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agentCards}
        </div>
      )}
    </div>
  );
});

export default DashboardPage;
