import React, { useState, useEffect } from "react";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Server, Clock, Terminal, Wifi, WifiOff } from "lucide-react";

const DashboardPage: React.FC = () => {
  const { ws, isConnected } = useWebSocket();
  const [messages, setMessages] = useState<string[]>([]);

  const { data: systemStatus, isLoading } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: async () => {
      // Placeholder for fetching system status
      return { status: "Online", uptime: "2 hours", commandsExecuted: 45 };
    },
  });

  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        setMessages((prev) => [...prev, event.data]);
      };
    }
  }, [ws]);

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

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

          <div className="mockup-code bg-base-300 text-base-content h-96 overflow-y-auto w-full custom-scrollbar">
            {messages.length > 0 ? (
              messages.slice(-15).map((msg, index) => (
                <pre key={index} data-prefix=">" className="text-success">
                  <code>{msg}</code>
                </pre>
              ))
            ) : (
              <div className="p-4 text-base-content/50 italic text-center pt-32">
                Waiting for commands...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
