import React from "react";
import { useQuery } from "@tanstack/react-query";
import { PhoneCall, AlertTriangle, PhoneOff } from "lucide-react";

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
  const { data: status, isLoading: statusLoading } = useQuery<DograhStatusResponse>({
    queryKey: ["dograh", "status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/dograh/status");
      if (!res.ok) {
        return { available: false, reason: `HTTP ${res.status}`, health: null };
      }
      return (await res.json()) as DograhStatusResponse;
    },
    refetchInterval: 15_000,
    retry: false,
  });

  const { data: workflows } = useQuery<DograhWorkflow[]>({
    queryKey: ["dograh", "workflows"],
    queryFn: async () => {
      const res = await fetch("/api/v1/dograh/workflows");
      if (!res.ok) return [];
      return (await res.json()) as DograhWorkflow[];
    },
    enabled: status?.available === true,
    refetchInterval: 30_000,
    retry: false,
  });

  if (statusLoading) {
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
    return (
      <div
        className="stats shadow bg-base-100 border border-base-content/10"
        data-testid="dograh-status-card"
        data-dograh-state="unavailable"
      >
        <div className="stat">
          <div className="stat-figure text-base-content/40">
            <PhoneOff size={32} />
          </div>
          <div className="stat-title">Dograh</div>
          <div className="stat-value text-2xl text-base-content/50">Offline</div>
          <div className="stat-desc text-xs truncate" title={status?.reason ?? ""}>
            {status?.reason ?? "not configured"}
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
