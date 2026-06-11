import React from "react";
import { PhoneIncoming, PhoneCall, PhoneOff } from "lucide-react";

export type DograhCallState = "ringing" | "in_call" | "ended" | "unknown";

export interface DograhCallStatePayload {
  state: DograhCallState;
  workflow_id: number | null;
  run_id: number | null;
}

interface CallStateBadgeProps {
  call: DograhCallStatePayload | null;
}

const CONFIG: Record<
  Exclude<DograhCallState, "unknown">,
  { label: string; badge: string; text: string; Icon: typeof PhoneCall; pulse: boolean }
> = {
  ringing: {
    label: "Ringing",
    badge: "badge-warning",
    text: "text-warning",
    Icon: PhoneIncoming,
    pulse: true,
  },
  in_call: {
    label: "In call",
    badge: "badge-success",
    text: "text-success",
    Icon: PhoneCall,
    pulse: true,
  },
  ended: {
    label: "Call ended",
    badge: "badge-ghost",
    text: "text-base-content/60",
    Icon: PhoneOff,
    pulse: false,
  },
};

/**
 * Compact live indicator for the Dograh call state broadcast over /ws.
 *
 * Reflects whatever the backend broadcasts via the
 * {type:'dograh_call_state', data:{state, workflow_id, run_id}} message.
 * When there is no active call (state 'unknown' or no payload yet) the badge
 * renders nothing so the dashboard stays unobtrusive.
 */
const CallStateBadge = React.memo(({ call }: CallStateBadgeProps) => {
  const state = call?.state ?? "unknown";

  // Idle / no active call: stay out of the way.
  if (state === "unknown") {
    return null;
  }

  const cfg = CONFIG[state];
  const { Icon } = cfg;

  // motion-safe: prefers-reduced-motion users get a static badge.
  const animate = cfg.pulse ? "motion-safe:animate-pulse" : "";

  const subtitle =
    call?.workflow_id != null
      ? `wf ${call.workflow_id}${call.run_id != null ? ` · run ${call.run_id}` : ""}`
      : null;

  return (
    <div
      className="stats shadow bg-base-100 border border-base-content/10"
      data-testid="dograh-call-state"
      data-call-state={state}
    >
      <div className="stat">
        <div className={`stat-figure ${cfg.text} ${animate}`} aria-hidden="true">
          <Icon size={32} />
        </div>
        <div className="stat-title flex items-center gap-2">
          Dograh Call
          <span className={`badge ${cfg.badge} badge-sm`}>{cfg.label.toLowerCase()}</span>
        </div>
        <div className={`stat-value text-2xl ${cfg.text}`}>{cfg.label}</div>
        <div className="stat-desc">{subtitle ?? "Live call status"}</div>
      </div>
    </div>
  );
});

CallStateBadge.displayName = "CallStateBadge";

export default CallStateBadge;
