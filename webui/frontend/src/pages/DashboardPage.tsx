import React, { useState, useEffect, useCallback } from "react";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Server, Clock, Terminal, Wifi, WifiOff, Send, Activity as AssessmentIcon } from "lucide-react";
import { apiService } from "../services/apiService";
import { fetchAgentStatus, Agent } from "../services/api";

const MAX_MESSAGES = 100;

const DashboardPage: React.FC = () => {
  const { ws, isConnected } = useWebSocket();
  const [messages, setMessages] = useState<string[]>([]);
  const [commandInput, setCommandInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;

    setIsSending(true);
    const cmd = commandInput;
    setCommandInput("");

    // Optimistically add to log
    setMessages(prev => [...prev, `> Executing: ${cmd}`].slice(-MAX_MESSAGES));

    try {
      await apiService.executeCommand(cmd);
    } catch (err: any) {
      setMessages(prev => [...prev, `Error: ${err.message}`].slice(-MAX_MESSAGES));
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
    refetchInterval: 30000,
  });

  const [realtimeStatus, setRealtimeStatus] = useState<any>(null);
  const systemStatus = { ...initialSystemStatus, ...realtimeStatus };

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
        setRealtimeStatus((prev: any) => ({
          ...prev,
          cpu: msg.data.cpu !== undefined ? `${Number(msg.data.cpu).toFixed(1)}` : prev?.cpu,
          memory: msg.data.memory !== undefined ? `${Number(msg.data.memory).toFixed(1)}` : prev?.memory,
        }));
        return;
      }
      // Fallback for non-JSON or other messages
      if (msg.data && typeof msg.data === "string") {
        setMessages((prev) => [...prev, msg.data].slice(-MAX_MESSAGES));
      }
    } catch {
      // Plain text message
      setMessages((prev) => [...prev, event.data].slice(-MAX_MESSAGES));
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
      <div className="flex justify-center items-center h-full">
        <span className="loading loading-spinner loading-lg text-primary"></span>
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
            <div className="stat-desc">Realtime stream</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="card bg-base-100 shadow-xl border border-base-content/10">
        <div className="card-body">
          <h3 className="card-title text-xl mb-4">Real-time Command Log</h3>

          <div className="mockup-code bg-base-300 text-base-content h-[20rem] overflow-y-auto w-full custom-scrollbar">
            {messages.length > 0 ? (
              messages.slice(-15).map((msg, index) => (
                <pre key={index} data-prefix=">" className={msg.startsWith("Error:") ? "text-error" : "text-success"}>
                  <code>{msg}</code>
                </pre>
              ))
            ) : (
              <div className="p-4 text-base-content/50 italic text-center pt-24">
                Waiting for commands...
              </div>
            )}
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
