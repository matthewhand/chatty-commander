/**
 * FakeWebSocket — a drop-in, never-connecting WebSocket replacement for the
 * static demo build. It immediately reports OPEN so the dashboard's connection
 * badge shows "Connected" (instead of being stuck "Reconnecting...") and emits
 * a few pre-scripted telemetry / voice-test frames so the live UI shows motion.
 *
 * No network is ever touched. Only installed when VITE_DEMO is truthy.
 */

type Listener = (ev: any) => void;

const TELEMETRY_INTERVAL_MS = 2500;

export class FakeWebSocket {
  // Standard readyState constants (mirror the real WebSocket interface).
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  readonly CONNECTING = 0;
  readonly OPEN = 1;
  readonly CLOSING = 2;
  readonly CLOSED = 3;

  url: string;
  readyState: number = FakeWebSocket.CONNECTING;
  binaryType: "blob" | "arraybuffer" = "blob";

  onopen: Listener | null = null;
  onclose: Listener | null = null;
  onerror: Listener | null = null;
  onmessage: Listener | null = null;

  private listeners: Record<string, Set<Listener>> = {};
  private timers: ReturnType<typeof setInterval | typeof setTimeout>[] = [];
  private isVoiceTest: boolean;

  constructor(url: string | URL) {
    this.url = String(url);
    this.isVoiceTest = this.url.includes("/ws/voice-test");

    // Defer "open" to a microtask/timeout so handlers assigned right after
    // construction (the typical `new WebSocket(); ws.onopen = ...` pattern) are
    // wired up before we fire.
    this.timers.push(
      setTimeout(() => {
        this.readyState = FakeWebSocket.OPEN;
        this.emit("open", { type: "open" });
        this.startScript();
      }, 0)
    );
  }

  addEventListener(type: string, cb: Listener): void {
    (this.listeners[type] ??= new Set()).add(cb);
  }

  removeEventListener(type: string, cb: Listener): void {
    this.listeners[type]?.delete(cb);
  }

  private emit(type: string, ev: any): void {
    const handler = (this as any)["on" + type] as Listener | null;
    if (typeof handler === "function") handler(ev);
    this.listeners[type]?.forEach((cb) => cb(ev));
  }

  private emitMessage(data: string): void {
    this.emit("message", { type: "message", data });
  }

  send(_data?: any): void {
    // Demo is one-way; the dashboard/voice-test pages send start frames which
    // we simply acknowledge by continuing our scripted output. No-op otherwise.
  }

  close(code = 1000, reason = ""): void {
    if (
      this.readyState === FakeWebSocket.CLOSED ||
      this.readyState === FakeWebSocket.CLOSING
    ) {
      return;
    }
    this.readyState = FakeWebSocket.CLOSING;
    this.timers.forEach((t) => clearInterval(t as any));
    this.timers = [];
    this.readyState = FakeWebSocket.CLOSED;
    this.emit("close", { type: "close", code, reason, wasClean: true });
  }

  private startScript(): void {
    if (this.isVoiceTest) {
      this.startVoiceTestScript();
    } else {
      this.startTelemetryScript();
    }
  }

  /** Emit {type:'telemetry', data:{cpu,memory}} frames the dashboard parses. */
  private startTelemetryScript(): void {
    const tick = () => {
      if (this.readyState !== FakeWebSocket.OPEN) return;
      // Gentle pseudo-random wander so the live chart shows movement.
      const cpu = 8 + Math.round(Math.random() * 30 * 10) / 10;
      const memory = 26 + Math.round(Math.random() * 12 * 10) / 10;
      this.emitMessage(JSON.stringify({ type: "telemetry", data: { cpu, memory } }));
    };
    // Fire one immediately, then on an interval.
    this.timers.push(setTimeout(tick, 400));
    this.timers.push(setInterval(tick, TELEMETRY_INTERVAL_MS));
  }

  /** Emit a short scripted dry-run pipeline for the Voice Test page. */
  private startVoiceTestScript(): void {
    const now = () => Date.now();
    const frames = [
      { stage: "listening", data: { message: "Demo dry-run — microphone is simulated." } },
      { stage: "wakeword", data: { wakeword: "hey_khum_puter", confidence: 0.97 } },
      { stage: "transcript", data: { text: "take a screenshot" } },
      { stage: "match", data: { command: "take_screenshot", score: 0.91 } },
      { stage: "dry_run_action", data: { action: "keypress", keys: "alt+print_screen", success: true } },
    ];
    let delay = 600;
    for (const f of frames) {
      this.timers.push(
        setTimeout(() => {
          if (this.readyState !== FakeWebSocket.OPEN) return;
          this.emitMessage(JSON.stringify({ ...f, ts: now() }));
        }, delay)
      );
      delay += 900;
    }
  }
}
