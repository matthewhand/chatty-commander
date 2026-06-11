import React, { useState } from "react";

/**
 * DemoBanner — a prominent, dismissible notice shown at the app root only in
 * the static demo build. Communicates that all data is pre-recorded and that
 * live voice/AI features require a local install. Dismissal is persisted in
 * localStorage so it stays hidden for the session/device once closed.
 *
 * Only mounted when VITE_DEMO is truthy (see index.tsx).
 */

const STORAGE_KEY = "demoBannerDismissed";

const DemoBanner: React.FC = () => {
  const [dismissed, setDismissed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore storage failures */
    }
    setDismissed(true);
  };

  return (
    <div
      role="status"
      data-testid="demo-banner"
      className="sticky top-0 z-50 w-full bg-warning text-warning-content shadow-md"
    >
      <div className="flex items-center gap-3 px-4 py-2 text-sm">
        <span className="badge badge-neutral badge-sm font-bold uppercase tracking-wide">
          Demo
        </span>
        <span className="flex-1 leading-snug">
          <strong>Demo mode</strong> — data is pre-recorded and static; no backend
          or API keys. Live voice/AI features require a local install.
        </span>
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss demo notice"
          className="btn btn-ghost btn-xs"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default DemoBanner;
