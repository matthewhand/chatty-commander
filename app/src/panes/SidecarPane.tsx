import React, { useState, useEffect } from "react";
import { useSidecarStore } from "../stores/sidecar";

const TABS = [
  { key: 'code', label: 'Code' },
  { key: 'tests', label: 'Tests' },
  { key: 'notes', label: 'Notes' },
  { key: 'diff', label: 'Diff' },
];

export default function SidecarPane() {
  const current = useSidecarStore(s => s.current);
  const close = useSidecarStore(s => s.close);
  const [tab, setTab] = useState<'code' | 'tests' | 'notes' | 'diff'>('code');
  const [comment, setComment] = useState('');
  const [avatarStatus, setAvatarStatus] = useState<
    "idle" | "launching" | "running" | "error"
  >("idle");

  useEffect(() => {
    if (current?.kind) setTab(current.kind);
  }, [current]);

  const launchAvatar = async () => {
    setAvatarStatus("launching");
    try {
      const response = await fetch("/api/v1/avatar/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        setAvatarStatus("running");
        setTimeout(() => setAvatarStatus("idle"), 3000); // Reset after 3 seconds
      } else {
        setAvatarStatus("error");
        setTimeout(() => setAvatarStatus("idle"), 3000);
      }
    } catch (error) {
      console.error("Failed to launch avatar:", error);
      setAvatarStatus("error");
      setTimeout(() => setAvatarStatus("idle"), 3000);
    }
  };

  const getStatusMessage = () => {
    switch (avatarStatus) {
      case "launching":
        return "Launching avatar...";
      case "running":
        return "Avatar launched successfully!";
      case "error":
        return "Failed to launch avatar. Check console.";
      default:
        return "";
    }
  };

  const getStatusColor = () => {
    switch (avatarStatus) {
      case "launching":
        return "text-yellow-400";
      case "running":
        return "text-green-400";
      case "error":
        return "text-red-400";
      default:
        return "";
    }
  };

  return (
    <section className="h-full flex flex-col bg-gray-900">
      {current ? (
        <>
          <header className="flex items-center justify-between p-2 border-b border-gray-700">
            <h2 className="font-semibold">{current?.title || 'Sidecar'}</h2>
            <button onClick={close} aria-label="Close" className="px-2">×</button>
          </header>
          <nav className="flex border-b border-gray-700">
            {TABS.map(t => (
              <button
                key={t.key}
                className={`px-3 py-1 text-sm ${tab === t.key ? 'bg-gray-800' : ''}`}
                onClick={() => setTab(t.key as any)}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="flex-1 overflow-auto p-2">
            {current?.snippet ? (
              <pre className="text-xs whitespace-pre-wrap">{current.snippet}</pre>
            ) : (
              <div className="text-gray-400">Open files and notes will appear here.</div>
            )}
          </div>
          <div className="p-2 border-t border-gray-700">
            <textarea
              className="w-full p-2 bg-gray-800"
              placeholder="Add a comment"
              value={comment}
              onChange={e => setComment(e.target.value)}
            />
            <button className="mt-2 px-3 py-1 bg-blue-600 rounded">Comment</button>
          </div>
        </>
      ) : (
        <div className="h-full p-2 bg-gray-900 space-y-4">
          <div>
            <h2 className="font-semibold mb-2">Avatar Mode</h2>
        <div className="space-y-3">
          <p className="text-sm text-gray-300">
            Launch a transparent desktop avatar that displays AI states and
            animations.
          </p>

          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-200">Features:</h3>
            <ul className="text-xs text-gray-400 space-y-1 ml-2">
              <li>• Transparent, frameless window</li>
              <li>• System tray integration</li>
              <li>• Real-time state animations</li>
              <li>• Always-on-top display</li>
            </ul>
          </div>

          <button
            onClick={launchAvatar}
            disabled={avatarStatus === "launching"}
            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-sm rounded transition-colors"
          >
            {avatarStatus === "launching" ? "Launching..." : "Launch Avatar"}
          </button>

          {avatarStatus !== "idle" && (
            <p className={`text-xs ${getStatusColor()}`}>
              {getStatusMessage()}
            </p>
          )}

          <div className="text-xs text-gray-500 space-y-1">
            <p>
              <strong>CLI Alternative:</strong>
            </p>
            <code className="bg-gray-800 px-2 py-1 rounded text-xs">
              uv run python -m src.chatty_commander.main --gui
            </code>
          </div>
        </div>
      </div>

      <div>
        <h2 className="font-semibold mb-2">Files & Notes</h2>
        <div className="text-sm text-gray-400">
          Open files and notes will appear here.
        </div>
      </div>
        </div>
      )}
    </section>
  );
}
