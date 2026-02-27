import React, { useState, useEffect, useRef, useCallback } from "react";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Server, Clock, Terminal, Wifi, WifiOff, Send, Activity as AssessmentIcon, AlertTriangle, Loader2 } from "lucide-react";
import { apiService } from "../services/apiService";
import { fetchAgentStatus, Agent } from "../services/api";
import { LogMessage, LogMessageItem } from "../components/LogMessageItem";

const MAX_MESSAGES = 100;

const DashboardPage: React.FC = () => {
  const { ws, isConnected, reconnectAttempt } = useWebSocket();
  const [messages, setMessages] = useState<LogMessage[]>([]);
  const [commandInput, setCommandInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  // Real-time telemetry state (updated via WebSocket telemetry messages)
  const [realtimeStatus, setRealtimeStatus] = useState<{ cpu?: string; memory?: string }>({});

  // Show toast for connection status
  const [showToast, setShowToast] = useState(false);

  useEffect(() => {
    // Show toast when connection is lost or reconnecting
    if (!isConnected) {
        setShowToast(true);
    } else {
        // Hide toast shortly after connection is restored
        const timer = setTimeout(() => setShowToast(false), 3000);
        return () => clearTimeout(timer);
    }
  }, [isConnected]);

  const addMessage = useCallback((message: Omit<LogMessage, "id" | "timestamp">) => {
    const newMessage: LogMessage = {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date(),
      ...message,
    };
    setMessages((prev) => [...prev, newMessage].slice(-MAX_MESSAGES));
  }, []); // setMessages is stable; no external deps needed

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    setIsSending(true);
    const cmd = commandInput;
    setCommandInput("");

    // Optimistically add to log
    addMessage({
      type: "command",
      content: `> Executing: ${cmd}`,
    });

    try {
      await apiService.executeCommand(cmd);
    } catch (err: any) {
      addMessage({
        type: "error",
        content: `Error: ${err.message}`,
      });
    } finally {
      setIsSending(false);
    }
  };

  const { data: systemStatus, isLoading } = useQuery({
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
    refetchInterval: 30000,
  });

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
      const payload = JSON.parse(event.data);

      // Handle telemetry messages without adding to log
      if (payload.type === "telemetry" && payload.data) {
        setRealtimeStatus((prev) => ({
          ...prev,
          cpu: payload.data.cpu !== undefined ? `${Number(payload.data.cpu).toFixed(1)}` : prev.cpu,
          memory: payload.data.memory !== undefined ? `${Number(payload.data.memory).toFixed(1)}` : prev.memory,
        }));
        return;
      }

      switch (payload.type) {
        case "state_change":
          addMessage({
            type: "state",
            content: `State changed to ${payload.data.new_state} (was ${payload.data.old_state})`,
            metadata: payload.data,
          });
          break;
        case "command_detected": {
          const confidence = (payload.data.confidence * 100).toFixed(1);
          addMessage({
            type: "command",
            content: `Command detected: ${payload.data.command} (${confidence}%)`,
            metadata: payload.data,
          });
          break;
        }
        case "system_event":
          addMessage({
            type: "system",
            content: `System Event: ${payload.data.message}`,
            metadata: payload.data,
          });
          break;
        case "connection_established":
          addMessage({
            type: "connection",
            content: `Connected to ChattyCommander (State: ${payload.data.current_state})`,
            metadata: payload.data,
          });
          break;
        case "heartbeat":
        case "pong":
          // Ignore keepalives
          return;
        default:
          addMessage({
            type: "info",
            content: `[${payload.type}] ${JSON.stringify(payload.data)}`,
            metadata: payload,
          });
      }
    } catch {
      addMessage({
        type: "info",
        content: event.data,
      });
    }
  }, [addMessage]); // addMessage is stable via useCallback

  useEffect(() => {
    if (!ws) return;
    // Use addEventListener to avoid overwriting other handlers
    ws.addEventListener("message", handleWsMessage);
    return () => {
      ws.removeEventListener("message", handleWsMessage);
    };
  }, [ws, handleWsMessage]);

  // Auto-scroll to bottom of log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  return (
    <div className="space-y-6 relative">
      <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
        Dashboard
      </h2>

      {/* Connection Toast */}
      {showToast && (
        <div className="toast toast-end z-50">
            {isConnected ? (
                <div className="alert alert-success shadow-lg animate-in slide-in-from-bottom-5">
                    <Wifi size={20} />
                    <span>Connected to Server</span>
                </div>
            ) : (
                <div className="alert alert-warning shadow-lg animate-in slide-in-from-bottom-5">
                    {reconnectAttempt > 0 ? (
                        <>
                            <Loader2 size={20} className="animate-spin" />
                            <div className="flex flex-col">
                                <span className="font-bold">Connection Lost</span>
                                <span className="text-xs">Reconnecting (Attempt {reconnectAttempt})...</span>
                            </div>
                        </>
                    ) : (
                        <>
                            <AlertTriangle size={20} />
                            <span>Connection Lost</span>
                        </>
                    )}
                </div>
            )}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

        <div className="stats shadow bg-base-100 border border-base-content/10">
          <div className="stat">
            <div className="stat-figure text-primary">
              <Server size={32} />
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
                <WifiOff size={32} className="text-error" />
              }
            </div>
            <div className="stat-title">WebSocket</div>
            <div className={`stat-value text-2xl ${isConnected ? 'text-success' : 'text-error'}`}>
              {isConnected ? "Connected" : "Offline"}
            </div>
            <div className="stat-desc">
                {reconnectAttempt > 0 ? `Reconnecting (${reconnectAttempt})...` : "Realtime stream"}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="card bg-base-100 shadow-xl border border-base-content/10">
        <div className="card-body">
          <h3 className="card-title text-xl mb-4">Real-time Command Log</h3>

          <div className="mockup-code bg-base-300 text-base-content h-[20rem] overflow-y-auto w-full custom-scrollbar p-0">
            <div className="p-4 min-h-full flex flex-col justify-end">
              {messages.length > 0 ? (
                messages.map((msg) => (
                  <LogMessageItem key={msg.id} message={msg} />
                ))
              ) : (
                <div className="p-4 text-base-content/30 italic text-center">
                  Waiting for system events...
                </div>
              )}
              <div ref={logEndRef} />
            </div>
          </div>

          <form onSubmit={handleSendCommand} className="mt-4 flex gap-2">
            <input
              type="text"
              placeholder="Type a command to execute..."
              className="input input-bordered w-full focus:input-primary"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              disabled={isSending || !isConnected}
            />
            <button
              type="submit"
              className={`btn btn-primary ${isSending ? 'loading' : ''}`}
              disabled={!commandInput.trim() || isSending || !isConnected}
            >
              {!isSending && <Send size={18} />}
              Execute
            </button>
          </form>
        </div>
      </div>

      {/* Agent Status Section */}
      <h3 className="text-2xl font-bold bg-gradient-to-r from-error to-warning bg-clip-text text-transparent mt-8 mb-4 flex items-center gap-2">
        <AssessmentIcon size={24} className="text-error" /> Agent Status
      </h3>

      {agentsError && (
        <div className="alert alert-error shadow-lg">
          <span>{(agentsErrObj as Error)?.message || "Failed to fetch agent status."}</span>
        </div>
      )}

      {agentsLoading ? (
        <div className="flex justify-center p-8">
          <span className="loading loading-spinner text-primary"></span>
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
                  <div className="alert alert-error shadow-sm text-xs py-2 my-2 rounded-lg">
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
};

export default DashboardPage;
