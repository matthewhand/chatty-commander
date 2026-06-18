import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PhoneCall, AlertTriangle, PhoneOff, ExternalLink } from "lucide-react";
import { useWebSocket } from "./WebSocketProvider";

interface DograhStatusResponse {
  available: boolean;
  reason: string | null;
  health: {
    status?: string;
    version?: string;
    deployment_mode?: string;
  } | null;
}

interface DograhWorkflow {
  id: number;
  name: string;
  status: string | null;
}

const DograhStatusCard = React.memo(() => {
  const { ws } = useWebSocket();

  // Push-driven status. Seeded once from the REST endpoint for the initial
  // load (so the card renders before any WS frame arrives, and as a fallback
  // when the socket isn't connected yet); thereafter the server pushes a
  // `dograh_status` frame on /ws connect and whenever availability changes.
  const [pushedStatus, setPushedStatus] = useState<DograhStatusResponse | null>(null);

  const { data: seededStatus, isLoading: statusLoading } = useQuery<DograhStatusResponse>({
    queryKey: ["dograh", "status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/dograh/status");
      if (!res.ok) {
        return { available: false, reason: `HTTP ${res.status}`, health: null };
      }
      return (await res.json()) as DograhStatusResponse;
    },
    retry: false,
  });

  // Subscribe the card to `dograh_status` pushes on the shared /ws channel.
  useEffect(() => {
    if (!ws) return;
    const handleMessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "dograh_status" && msg.data) {
          setPushedStatus({
            available: msg.data.available ?? false,
            reason: msg.data.reason ?? null,
            health: msg.data.health ?? null,
          });
        }
      } catch {
        // Non-JSON / unrelated frame — ignore.
      }
    };
    ws.addEventListener("message", handleMessage);
    return () => {
      ws.removeEventListener("message", handleMessage);
    };
  }, [ws]);

  // Pushed state wins once present; otherwise fall back to the seeded fetch.
  const status = pushedStatus ?? seededStatus;

  const { data: workflows } = useQuery<DograhWorkflow[]>({
    queryKey: ["dograh", "workflows"],
    queryFn: async () => {
      const res = await fetch("/api/v1/dograh/workflows");
      if (!res.ok) return [];
      return (await res.json()) as DograhWorkflow[];
    },
    enabled: status?.available === true,
    retry: false,
  });

  if (statusLoading && !status) {
    return (
      <div
        className="stats shadow bg-base-100 border border-base-content/10"
        aria-busy="true"
        aria-label="Loading Dograh status"
      >
        <div className="stat">
          <div className="stat-figure text-base-content/30">
            <PhoneCall size={32} />
          </div>
          <div className="stat-title">Dograh</div>
          <div className="stat-value text-2xl text-base-content/30">…</div>
          <div className="stat-desc">checking…</div>
        </div>
      </div>
    );
  }

  if (!status?.available) {
    // Not-configured is an optional, neutral state — not a failure. Use an
    // info treatment (not error red) and offer a clear "Set up / Learn more"
    // affordance so users understand it's available to enable, not broken.
    return (
      <div
        className="stats shadow bg-base-100 border border-info/30"
        data-testid="dograh-status-card"
        data-dograh-state="unavailable"
      >
        <div className="stat">
          <div className="stat-figure text-info/60">
            <PhoneOff size={32} />
          </div>
          <div className="stat-title">Dograh</div>
          <div className="stat-value text-2xl text-info/80">Offline</div>
          <div
            className="stat-desc text-xs whitespace-normal leading-snug max-w-[16rem]"
            title={status?.reason ?? ""}
          >
            Optional voice-call integration — not configured.
          </div>
          <div className="stat-actions mt-1">
            <a
              href="https://github.com/dograh/dograh"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-xs btn-info btn-outline gap-1"
            >
              <ExternalLink size={12} />
              Set up · Learn more
            </a>
          </div>
        </div>
      </div>
    );
  }

  const version = status.health?.version ?? "unknown";
  const wfCount = workflows?.length ?? 0;

  return (
    <div
      className="stats shadow bg-base-100 border border-base-content/10"
      data-testid="dograh-status-card"
      data-dograh-state="online"
    >
      <div className="stat">
        <div className="stat-figure text-success">
          <PhoneCall size={32} />
        </div>
        <div className="stat-title flex items-center gap-2">
          Dograh
          <span className="badge badge-success badge-sm">online</span>
        </div>
        <div className="stat-value text-success text-2xl">v{version}</div>
        <div className="stat-desc flex items-center gap-1">
          {wfCount === 0 && <AlertTriangle size={12} className="text-warning" />}
          {wfCount} workflow{wfCount === 1 ? "" : "s"}
        </div>
      </div>
    </div>
  );
});

DograhStatusCard.displayName = "DograhStatusCard";

export default DograhStatusCard;
