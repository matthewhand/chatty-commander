import React, { useCallback, useEffect, useRef, useState } from "react";
import { Mic, MicOff, Send, Wifi, WifiOff, Info, AlertTriangle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

/**
 * Single source of truth for the voice-test WebSocket path. The backend
 * endpoint (dry-run voice pipeline) is mounted at this path.
 */
export const VOICE_TEST_WS_PATH = "/ws/voice-test";

/** Mirrors how WebSocketProvider builds the /ws URL, including the auth token. */
export function buildVoiceTestWsUrl(noAuth?: boolean): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  let wsUrl = `${protocol}//${window.location.host}${VOICE_TEST_WS_PATH}`;
  const token = localStorage.getItem("auth_token");
  if (token && !noAuth) {
    wsUrl += `?token=${token}`;
  }
  return wsUrl;
}

export type MicState = "idle" | "requesting" | "denied" | "active";
type WsStatus = "connecting" | "connected" | "disconnected";

export interface StageEvent {
  stage: string;
  data: Record<string, unknown>;
  ts: number;
  receivedAt: number;
}

const STAGE_LABELS: Record<string, string> = {
  listening: "Listening",
  wakeword: "Wake word",
  transcript: "Transcript",
  match: "Command match",
  action: "Dry-run action",
  dry_run_action: "Dry-run action",
  "dry-run": "Dry-run action",
  error: "Error",
};

const MAX_EVENTS = 200;
const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_RECONNECT_DELAY_MS = 1000;

const isFailureEvent = (e: StageEvent): boolean =>
  e.stage === "error" ||
  e.data?.success === false ||
  typeof e.data?.error === "string";

/** Normalise a server ts (epoch seconds or ms) delta into milliseconds. */
const deltaMs = (prev: number, curr: number): number => {
  const d = curr - prev;
  // Epoch-seconds timestamps are ~1.7e9; epoch-ms are ~1.7e12.
  return Math.round(curr > 1e12 ? d : d * 1000);
};

const summariseData = (data: Record<string, unknown>): string => {
  if (!data || typeof data !== "object") return "";
  const parts: string[] = [];
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) continue;
    parts.push(`${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`);
  }
  return parts.join(" · ");
};

const VoiceTestPage: React.FC = () => {
  useEffect(() => {
    document.title = "Voice Test | ChattyCommander";
  }, []);

  const { user } = useAuth();

  // --- WebSocket state ---
  const [wsStatus, setWsStatus] = useState<WsStatus>("connecting");
  const [events, setEvents] = useState<StageEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptRef = useRef(0);
  const shouldReconnectRef = useRef(true);

  // --- Microphone state ---
  const [micState, setMicState] = useState<MicState>("idle");
  const [level, setLevel] = useState(0);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const [textInput, setTextInput] = useState("");

  const connect = useCallback(() => {
    if (!shouldReconnectRef.current) return;
    setWsStatus("connecting");
    const socket = new WebSocket(buildVoiceTestWsUrl(user?.noAuth));

    socket.onopen = () => {
      reconnectAttemptRef.current = 0;
      setWsStatus("connected");
      // Backend contract: announce the session in dry-run mode.
      socket.send(JSON.stringify({ type: "start", dry_run: true }));
    };

    socket.onmessage = (event: MessageEvent) => {
      if (typeof event.data !== "string") return;
      try {
        const parsed = JSON.parse(event.data);
        if (parsed && typeof parsed.stage === "string") {
          const stageEvent: StageEvent = {
            stage: parsed.stage,
            data: parsed.data && typeof parsed.data === "object" ? parsed.data : {},
            ts: typeof parsed.ts === "number" ? parsed.ts : Date.now(),
            receivedAt: Date.now(),
          };
          setEvents((prev) => [...prev, stageEvent].slice(-MAX_EVENTS));
        }
      } catch {
        // Ignore non-JSON frames (keep-alives etc.)
      }
    };

    socket.onclose = () => {
      setWsStatus("disconnected");
      wsRef.current = null;
      if (!shouldReconnectRef.current) return;
      if (reconnectAttemptRef.current < MAX_RECONNECT_ATTEMPTS) {
        const attempt = reconnectAttemptRef.current;
        const delay = Math.min(30000, BASE_RECONNECT_DELAY_MS * Math.pow(1.5, attempt));
        reconnectTimerRef.current = setTimeout(() => {
          reconnectAttemptRef.current += 1;
          connect();
        }, delay);
      }
    };

    socket.onerror = () => {
      // onclose follows; nothing else to do.
    };

    wsRef.current = socket;
  }, [user?.noAuth]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    connect();
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      const socket = wsRef.current;
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
      wsRef.current = null;
    };
  }, [connect]);

  // --- Microphone handling ---
  const stopMic = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    try {
      recorderRef.current?.stop();
    } catch {
      /* recorder may already be inactive */
    }
    recorderRef.current = null;
    try {
      audioCtxRef.current?.close();
    } catch {
      /* already closed */
    }
    audioCtxRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setLevel(0);
    setMicState("idle");
  }, []);

  const startMic = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicState("denied");
      return;
    }
    setMicState("requesting");
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setMicState("denied");
      return;
    }
    streamRef.current = stream;
    setMicState("active");

    // Input level meter via AnalyserNode (skipped where AudioContext is unavailable).
    const AudioCtx: typeof AudioContext | undefined =
      window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (AudioCtx) {
      try {
        const ctx = new AudioCtx();
        audioCtxRef.current = ctx;
        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        const buffer = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          analyser.getByteTimeDomainData(buffer);
          let sum = 0;
          for (let i = 0; i < buffer.length; i++) {
            const v = (buffer[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / buffer.length);
          setLevel(Math.min(100, Math.round(rms * 300)));
          rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
      } catch {
        /* meter is best-effort */
      }
    }

    // Stream audio chunks to the backend while the socket is open.
    if (typeof MediaRecorder !== "undefined") {
      try {
        const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
        recorder.ondataavailable = (e: BlobEvent) => {
          if (e.data && e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(e.data);
          }
        };
        recorder.start(250);
        recorderRef.current = recorder;
      } catch {
        /* audio streaming is best-effort; text simulation always works */
      }
    }
  }, []);

  // Stop everything on unmount.
  useEffect(() => stopMic, [stopMic]);

  const handleMicToggle = () => {
    if (micState === "active") {
      stopMic();
    } else if (micState === "idle" || micState === "denied") {
      void startMic();
    }
  };

  const sendText = (e: React.FormEvent) => {
    e.preventDefault();
    const text = textInput.trim();
    if (!text) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "text", text }));
      setTextInput("");
    }
  };

  const micButtonLabel =
    micState === "active"
      ? "Stop microphone"
      : micState === "requesting"
        ? "Requesting microphone access..."
        : "Enable microphone";

  return (
    <div className="space-y-6" data-testid="voice-test-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-3xl font-bold">Voice Test</h1>
        <span
          data-testid="voice-ws-status"
          className={`badge gap-2 ${
            wsStatus === "connected"
              ? "badge-success"
              : wsStatus === "connecting"
                ? "badge-warning"
                : "badge-error"
          }`}
        >
          {wsStatus === "connected" ? <Wifi size={14} /> : <WifiOff size={14} />}
          {wsStatus === "connected"
            ? "Connected"
            : wsStatus === "connecting"
              ? "Connecting..."
              : "Disconnected — retrying"}
        </span>
      </div>

      <div className="alert alert-info" role="status" data-testid="dry-run-banner">
        <Info size={18} />
        <span>Dry-run mode: detected commands are reported, not executed.</span>
      </div>

      {/* Microphone controls */}
      <div className="card bg-base-100 shadow">
        <div className="card-body space-y-4">
          <h2 className="card-title text-lg">Microphone</h2>

          {micState === "denied" && (
            <div className="alert alert-error" role="alert" data-testid="mic-denied-alert">
              <AlertTriangle size={18} />
              <span>
                Microphone access was denied or is unavailable. Check your browser
                permissions, then try again. You can still use the text simulation below.
              </span>
            </div>
          )}

          <div className="flex items-center gap-4 flex-wrap">
            <button
              type="button"
              className={`btn gap-2 ${micState === "active" ? "btn-error" : "btn-primary"}`}
              onClick={handleMicToggle}
              disabled={micState === "requesting"}
              aria-label={micButtonLabel}
              data-testid="mic-toggle"
            >
              {micState === "active" ? <MicOff size={18} /> : <Mic size={18} />}
              {micButtonLabel}
            </button>
            <span className="text-sm text-base-content/70" data-testid="mic-state">
              {micState === "idle" && "Microphone off"}
              {micState === "requesting" && "Waiting for permission..."}
              {micState === "denied" && "Permission denied"}
              {micState === "active" && "Listening — audio is streaming to the server"}
            </span>
          </div>

          {micState === "active" && (
            <div className="space-y-1">
              <span className="text-xs text-base-content/60">Input level</span>
              <div
                role="meter"
                aria-label="Microphone input level"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={level}
                data-testid="voice-level-meter"
                className="w-full max-w-md h-3 bg-base-300 rounded-full overflow-hidden"
              >
                <div
                  className="h-full bg-success transition-all duration-75"
                  style={{ width: `${level}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Text simulation — works without a microphone or browser audio support */}
      <div className="card bg-base-100 shadow">
        <div className="card-body space-y-2">
          <h2 className="card-title text-lg">Simulate a voice command</h2>
          <p className="text-sm text-base-content/60">
            Sends text straight into the wakeword → transcript → match pipeline, as if it had
            been spoken.
          </p>
          <form onSubmit={sendText} className="flex gap-2 flex-wrap">
            <input
              type="text"
              className="input input-bordered flex-1 min-w-48"
              placeholder="e.g. hey chatty open browser"
              aria-label="Simulate a voice command"
              data-testid="voice-simulate-input"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
            />
            <button
              type="submit"
              className="btn btn-secondary gap-2"
              disabled={wsStatus !== "connected" || !textInput.trim()}
              aria-label="Send simulated command"
              data-testid="voice-simulate-send"
            >
              <Send size={16} />
              Send
            </button>
          </form>
        </div>
      </div>

      {/* Live pipeline feedback */}
      <div className="card bg-base-100 shadow">
        <div className="card-body">
          <div className="flex items-center justify-between">
            <h2 className="card-title text-lg">Pipeline feedback</h2>
            {events.length > 0 && (
              <button
                type="button"
                className="btn btn-ghost btn-xs"
                onClick={() => setEvents([])}
                aria-label="Clear timeline"
              >
                Clear
              </button>
            )}
          </div>

          {events.length === 0 ? (
            <div
              className="text-center py-10 text-base-content/60"
              data-testid="voice-timeline-empty"
            >
              <p className="font-medium">No pipeline events yet.</p>
              <p className="text-sm mt-1">
                Enable the microphone and speak, or send a simulated command above. Each
                stage — listening, wake word, transcript, command match, dry-run action —
                will appear here as the server processes it.
              </p>
            </div>
          ) : (
            <ol className="space-y-2" data-testid="voice-stage-timeline" aria-label="Pipeline stage timeline">
              {events.map((event, i) => {
                const failure = isFailureEvent(event);
                const prev = i > 0 ? events[i - 1] : null;
                const delta = prev ? deltaMs(prev.ts, event.ts) : null;
                return (
                  <li
                    key={`${event.receivedAt}-${i}`}
                    data-testid="voice-stage-event"
                    data-stage={event.stage}
                    data-status={failure ? "failure" : "success"}
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      failure
                        ? "border-error/40 bg-error/10"
                        : "border-success/30 bg-success/5"
                    }`}
                  >
                    <span
                      className={`badge badge-sm mt-0.5 ${failure ? "badge-error" : "badge-success"}`}
                    >
                      {STAGE_LABELS[event.stage] ?? event.stage}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm break-words">
                        {summariseData(event.data) || "—"}
                      </div>
                    </div>
                    <span className="text-xs font-mono text-base-content/50 whitespace-nowrap">
                      {delta !== null ? `+${delta}ms` : "start"}
                    </span>
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceTestPage;
