import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Mic,
  MicOff,
  Send,
  Wifi,
  WifiOff,
  Info,
  AlertTriangle,
  Radio,
  CheckCircle2,
  Circle,
  Loader2,
  FileText,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/ToastProvider";

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
/** How long to wait for the next stage event before warning of a stall. */
const PROCESSING_TIMEOUT_MS = 8000;
/** Throttle interval for the VU meter's aria-valuenow announcements (ms). */
const VU_ARIA_THROTTLE_MS = 500;

/** Example wake-word phrases offered as quick-fill chips. */
const WAKE_WORD_EXAMPLES = [
  "hey chatty open browser",
  "hey chatty take screenshot",
  "hey chatty what time is it",
];

const isFailureEvent = (e: StageEvent): boolean =>
  e.stage === "error" ||
  e.data?.success === false ||
  e.data?.matched === false ||
  typeof e.data?.error === "string";

const isWakeWordStage = (stage: string): boolean =>
  stage === "wakeword" || stage === "wake_word" || stage === "wake-word";

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

/** A single tick row in the verify-setup checklist. */
function ChecklistRow({ done, label }: { done: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2 text-sm" data-checked={done}>
      {done ? (
        <CheckCircle2 size={16} className="text-success shrink-0" aria-hidden="true" />
      ) : (
        <Circle size={16} className="text-base-content/30 shrink-0" aria-hidden="true" />
      )}
      <span className={done ? "" : "text-base-content/60"}>{label}</span>
      <span className="sr-only">{done ? " — done" : " — pending"}</span>
    </li>
  );
}

const VoiceTestPage: React.FC = () => {
  useEffect(() => {
    document.title = "Voice Test | ChattyCommander";
  }, []);

  const { user } = useAuth();
  const { addToast } = useToast();

  // --- WebSocket state ---
  const [wsStatus, setWsStatus] = useState<WsStatus>("connecting");
  const [events, setEvents] = useState<StageEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptRef = useRef(0);
  const shouldReconnectRef = useRef(true);

  // --- Microphone state ---
  const [micState, setMicState] = useState<MicState>("idle");
  const [recorderRunning, setRecorderRunning] = useState(false);
  const [level, setLevel] = useState(0);
  const [ariaLevel, setAriaLevel] = useState(0);
  const ariaLevelThrottleRef = useRef(0);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const [textInput, setTextInput] = useState("");

  // --- Device selection ---
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");

  // --- Processing / latency indicator ---
  const [processing, setProcessing] = useState(false);
  const [processingStalled, setProcessingStalled] = useState(false);
  const processingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refreshDevices = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    try {
      const all = await navigator.mediaDevices.enumerateDevices();
      setDevices(all.filter((d) => d.kind === "audioinput"));
    } catch {
      /* enumeration is best-effort */
    }
  }, []);

  // Enumerate devices on mount and whenever the device set changes.
  useEffect(() => {
    void refreshDevices();
    const md = navigator.mediaDevices;
    if (!md?.addEventListener) return;
    md.addEventListener("devicechange", refreshDevices);
    return () => md.removeEventListener("devicechange", refreshDevices);
  }, [refreshDevices]);

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
          // A stage arrived: the pipeline is alive again.
          setProcessing(false);
          setProcessingStalled(false);
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

  // --- Processing indicator lifecycle ---
  const beginProcessing = useCallback(() => {
    setProcessing(true);
    setProcessingStalled(false);
    if (processingTimerRef.current) clearTimeout(processingTimerRef.current);
    processingTimerRef.current = setTimeout(() => {
      setProcessingStalled(true);
    }, PROCESSING_TIMEOUT_MS);
  }, []);

  // Clear the stall timer once processing finishes (or on unmount).
  useEffect(() => {
    if (!processing && processingTimerRef.current) {
      clearTimeout(processingTimerRef.current);
      processingTimerRef.current = null;
    }
    return () => {
      if (processingTimerRef.current) {
        clearTimeout(processingTimerRef.current);
        processingTimerRef.current = null;
      }
    };
  }, [processing]);

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
    setRecorderRunning(false);
    try {
      audioCtxRef.current?.close();
    } catch {
      /* already closed */
    }
    audioCtxRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setLevel(0);
    setAriaLevel(0);
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
      // Honour the chosen input device rather than silently grabbing the default.
      const audioConstraint: MediaTrackConstraints | boolean = selectedDeviceId
        ? { deviceId: { exact: selectedDeviceId } }
        : true;
      stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraint });
    } catch {
      setMicState("denied");
      return;
    }
    streamRef.current = stream;
    setMicState("active");
    // Device labels are only populated after permission is granted.
    void refreshDevices();

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
          const next = Math.min(100, Math.round(rms * 300));
          setLevel(next);
          // Throttle the value we expose to assistive tech so it doesn't
          // spam screen-reader announcements every animation frame.
          const now = Date.now();
          if (now - ariaLevelThrottleRef.current >= VU_ARIA_THROTTLE_MS) {
            ariaLevelThrottleRef.current = now;
            setAriaLevel(next);
          }
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
        setRecorderRunning(true);
      } catch {
        /* audio streaming is best-effort; text simulation always works */
        setRecorderRunning(false);
      }
    }
  }, [selectedDeviceId, refreshDevices]);

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
      beginProcessing();
    }
  };

  // --- Derived state ---
  const micActive = micState === "active";
  // Honest streaming state: only truly streaming when recorder is running AND
  // the socket is open. Warn when the mic is on but the link is broken.
  const streaming = micActive && recorderRunning && wsStatus === "connected";
  const micButtonLabel =
    micState === "active"
      ? "Stop microphone"
      : micState === "requesting"
        ? "Requesting microphone access..."
        : "Enable microphone";

  // transcription_available is reported in the `listening` stage data.
  const transcriptionUnavailable = useMemo(() => {
    const listening = [...events].reverse().find((e) => e.stage === "listening");
    if (!listening) return false;
    return listening.data?.transcription_available === false;
  }, [events]);

  // Latest transcript text for the dedicated panel.
  const latestTranscript = useMemo(() => {
    const t = [...events].reverse().find((e) => e.stage === "transcript");
    if (!t) return null;
    const text = t.data?.text;
    return typeof text === "string" ? text : "";
  }, [events]);

  // Verify-setup checklist progress.
  const wakeWordSeen = useMemo(() => events.some((e) => isWakeWordStage(e.stage)), [events]);
  const commandMatched = useMemo(
    () => events.some((e) => e.stage === "match" && e.data?.matched === true),
    [events],
  );

  const wakeWordJustDetected = useMemo(() => {
    // Highlight when the most recent event is a wake-word stage.
    const last = events[events.length - 1];
    return last ? isWakeWordStage(last.stage) : false;
  }, [events]);

  // Toast when the mic is on but streaming has silently broken.
  const prevStreamProblemRef = useRef(false);
  useEffect(() => {
    const problem = micActive && (!recorderRunning || wsStatus !== "connected");
    if (problem && !prevStreamProblemRef.current) {
      addToast(
        wsStatus !== "connected"
          ? "Microphone is on but the server connection is down — audio is not reaching the pipeline."
          : "Microphone is on but audio recording failed to start — use text simulation instead.",
        "warning",
      );
    }
    prevStreamProblemRef.current = problem;
  }, [micActive, recorderRunning, wsStatus, addToast]);

  return (
    <div className="space-y-6" data-testid="voice-test-page">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-3xl font-bold">Voice Test</h1>
          <p className="text-base-content/70 mt-1 max-w-2xl" data-testid="voice-test-subtitle">
            Confirm your mic, wake-word detection and command matching work end-to-end —
            no real actions run. Speak (or type) a command and watch each pipeline stage
            light up below; matched commands are reported, never executed.
          </p>
        </div>
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
        <span>
          <strong>What to expect:</strong> dry-run mode — detected commands are reported, not
          executed. You will see stages for listening, wake word, transcript, command match and a
          described (but not performed) action.
        </span>
      </div>

      {/* Verify-setup checklist */}
      <div className="card bg-base-100 shadow" data-testid="voice-checklist">
        <div className="card-body py-4">
          <h2 className="card-title text-base">Verify setup</h2>
          <ul className="grid gap-1 sm:grid-cols-2">
            <ChecklistRow done={wsStatus === "connected"} label="Server connected" />
            <ChecklistRow done={streaming} label="Microphone active and streaming" />
            <ChecklistRow done={wakeWordSeen} label="Wake word detected" />
            <ChecklistRow done={commandMatched} label="Command matched" />
          </ul>
        </div>
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

          {/* Honest warning: mic on but not actually streaming. */}
          {micActive && !streaming && (
            <div className="alert alert-warning" role="alert" data-testid="mic-stream-warning">
              <AlertTriangle size={18} />
              <span>
                {wsStatus !== "connected"
                  ? "Microphone is on, but the server connection is down — audio is not reaching the pipeline."
                  : "Microphone is on, but audio recording failed to start — use the text simulation below."}
              </span>
            </div>
          )}

          {/* Input device picker */}
          <div className="form-control max-w-md">
            <label className="label py-1" htmlFor="voice-input-device">
              <span className="label-text">Input device</span>
            </label>
            <select
              id="voice-input-device"
              className="select select-bordered select-sm"
              data-testid="voice-device-select"
              aria-label="Microphone input device"
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              disabled={micState === "requesting"}
            >
              <option value="">System default</option>
              {devices.map((d, i) => (
                <option key={d.deviceId || `device-${i}`} value={d.deviceId}>
                  {d.label || `Microphone ${i + 1}`}
                </option>
              ))}
            </select>
            {devices.length === 0 && (
              <span className="text-xs text-base-content/50 mt-1">
                Device names appear after you grant microphone permission.
              </span>
            )}
          </div>

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
              {micState === "active" &&
                (streaming
                  ? "Listening — streaming to server"
                  : "Microphone on — not streaming")}
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
                aria-valuenow={ariaLevel}
                aria-valuetext={`Input level ${ariaLevel} percent`}
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
          <div className="flex flex-wrap gap-2" data-testid="wake-word-chips">
            <span className="text-xs text-base-content/50 self-center">Try:</span>
            {WAKE_WORD_EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                className="badge badge-outline badge-sm gap-1 hover:badge-primary cursor-pointer"
                onClick={() => setTextInput(example)}
                data-testid="wake-word-chip"
              >
                {example}
              </button>
            ))}
          </div>
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
            <span
              className={wsStatus !== "connected" || !textInput.trim() ? "tooltip tooltip-left" : ""}
              data-tip={
                wsStatus !== "connected"
                  ? "Disabled — not connected to the server"
                  : !textInput.trim()
                    ? "Enter a command to send"
                    : undefined
              }
            >
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
            </span>
          </form>
        </div>
      </div>

      {/* Transcript panel */}
      <div className="card bg-base-100 shadow" data-testid="voice-transcript-panel">
        <div className="card-body py-4">
          <h2 className="card-title text-base flex items-center gap-2">
            <FileText size={18} /> Transcript
          </h2>
          {transcriptionUnavailable ? (
            <div
              className="alert alert-warning"
              role="status"
              data-testid="transcript-unavailable"
            >
              <Info size={18} />
              <span>
                Speech-to-text isn't configured on the server — wake word + command matching
                still work. Use the text simulation above to test the pipeline.
              </span>
            </div>
          ) : latestTranscript !== null ? (
            <p className="font-mono text-sm break-words" data-testid="transcript-text">
              {latestTranscript || "(empty transcript)"}
            </p>
          ) : (
            <p className="text-sm text-base-content/50" data-testid="transcript-empty">
              Recognized text will appear here once the server returns a transcript.
            </p>
          )}
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

          {/* Prominent wake-word affordance */}
          {wakeWordJustDetected && (
            <div
              className="alert alert-success animate-pulse"
              role="status"
              data-testid="wake-word-detected"
            >
              <Radio size={18} />
              <span className="font-semibold">Wake word detected!</span>
            </div>
          )}

          {/* Processing / latency indicator */}
          {processing && (
            <div
              className={`alert ${processingStalled ? "alert-warning" : "alert-info"}`}
              role="status"
              data-testid="voice-processing"
            >
              {processingStalled ? (
                <AlertTriangle size={18} />
              ) : (
                <Loader2 size={18} className="animate-spin" />
              )}
              <span>
                {processingStalled
                  ? "Still waiting on the pipeline — it may be stalled. Check the server connection."
                  : "Processing…"}
              </span>
            </div>
          )}

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
            <ol
              className="space-y-2"
              data-testid="voice-stage-timeline"
              aria-label="Pipeline stage timeline"
              role="log"
              aria-live="polite"
            >
              {events.map((event, i) => {
                const failure = isFailureEvent(event);
                const wake = isWakeWordStage(event.stage);
                const prev = i > 0 ? events[i - 1] : null;
                const delta = prev ? deltaMs(prev.ts, event.ts) : null;
                return (
                  <li
                    key={`${event.receivedAt}-${i}`}
                    data-testid="voice-stage-event"
                    data-stage={event.stage}
                    data-status={failure ? "failure" : "success"}
                    data-wakeword={wake ? "true" : undefined}
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      wake
                        ? "border-primary/60 bg-primary/10 ring-1 ring-primary/40"
                        : failure
                          ? "border-error/40 bg-error/10"
                          : "border-success/30 bg-success/5"
                    }`}
                  >
                    {wake ? (
                      <span
                        className="badge badge-sm badge-primary gap-1 mt-0.5"
                        data-testid="wake-word-badge"
                      >
                        <Radio size={12} />
                        {STAGE_LABELS[event.stage] ?? event.stage}
                      </span>
                    ) : (
                      <span
                        className={`badge badge-sm mt-0.5 ${failure ? "badge-error" : "badge-success"}`}
                      >
                        {STAGE_LABELS[event.stage] ?? event.stage}
                      </span>
                    )}
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

      {/* Cross-link to command editing */}
      <div className="text-sm text-base-content/70">
        Want to change what these commands do?{" "}
        <Link to="/commands" className="link link-primary inline-flex items-center gap-1" data-testid="edit-commands-link">
          Edit commands <ExternalLink size={14} />
        </Link>
      </div>
    </div>
  );
};

export default VoiceTestPage;
