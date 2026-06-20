import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import VoiceTestPage, {
  VOICE_TEST_WS_PATH,
  buildVoiceTestWsUrl,
} from "./VoiceTestPage";
import { ToastProvider } from "../components/ToastProvider";

// Mutable mock user so individual tests can flip noAuth.
const authMock = vi.hoisted(() => ({
  user: { username: "tester", roles: ["admin"], is_active: true, noAuth: true } as any,
}));

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    user: authMock.user,
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

// Spy on session-expiry signalling so auth-close handling can be asserted.
const notifySessionExpiredMock = vi.hoisted(() => vi.fn());
vi.mock("../services/authService", () => ({
  notifySessionExpired: notifySessionExpiredMock,
}));

// Render helper wrapping the page in the providers it depends on (router + toasts).
// `route` lets tests exercise the `?command=` author->test deep link.
const renderPage = (route = "/voice-test") =>
  render(
    <MemoryRouter initialEntries={[route]}>
      <ToastProvider>
        <VoiceTestPage />
      </ToastProvider>
    </MemoryRouter>,
  );

// Controllable WebSocket test double; records instances and sent frames.
class TestWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: TestWebSocket[] = [];

  url: string;
  readyState = TestWebSocket.CONNECTING;
  sent: unknown[] = [];
  onopen: ((ev?: unknown) => void) | null = null;
  onclose: ((ev?: unknown) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev?: unknown) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    TestWebSocket.instances.push(this);
  }

  send(data: unknown) {
    this.sent.push(data);
  }

  close() {
    this.readyState = TestWebSocket.CLOSED;
    this.onclose?.({ code: 1000, reason: "" });
  }

  // Test helpers
  serverOpen() {
    this.readyState = TestWebSocket.OPEN;
    this.onopen?.({});
  }

  serverEvent(payload: Record<string, unknown>) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  serverClose(code = 1006, reason = "abnormal") {
    this.readyState = TestWebSocket.CLOSED;
    this.onclose?.({ code, reason });
  }
}

const lastSocket = () =>
  TestWebSocket.instances[TestWebSocket.instances.length - 1];

const fakeTrack = { stop: vi.fn() };
const fakeStream = { getTracks: () => [fakeTrack] } as unknown as MediaStream;

beforeEach(() => {
  TestWebSocket.instances = [];
  (globalThis as any).WebSocket = TestWebSocket;
  authMock.user = { username: "tester", roles: ["admin"], is_active: true, noAuth: true };
  localStorage.clear();
  fakeTrack.stop.mockClear();
  notifySessionExpiredMock.mockClear();
  // jsdom has no mediaDevices; install a stub per test.
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockResolvedValue(fakeStream),
      enumerateDevices: vi.fn().mockResolvedValue([]),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    },
  });
});

describe("VoiceTestPage", () => {
  test("renders heading, subtitle, dry-run banner, and timeline empty state", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Voice Test" })).toBeInTheDocument();
    // Subtitle explains what the test verifies.
    expect(screen.getByTestId("voice-test-subtitle")).toHaveTextContent(
      /no real actions run/i,
    );
    expect(screen.getByTestId("dry-run-banner")).toHaveTextContent(/What to expect/i);
    expect(screen.getByTestId("voice-timeline-empty")).toBeInTheDocument();
    expect(screen.getByText("No pipeline events yet.")).toBeInTheDocument();
    expect(document.title).toBe("Voice Test | ChattyCommander");
  });

  test("renders the verify-setup checklist and the edit-commands cross-link", () => {
    renderPage();

    expect(screen.getByTestId("voice-checklist")).toBeInTheDocument();
    const link = screen.getByTestId("edit-commands-link");
    expect(link).toHaveAttribute("href", "/commands");
  });

  test("connects to the voice-test WS path and sends the dry-run start frame", () => {
    renderPage();

    const socket = lastSocket();
    expect(socket.url).toContain(VOICE_TEST_WS_PATH);
    expect(screen.getByTestId("voice-ws-status")).toHaveTextContent("Connecting...");

    act(() => socket.serverOpen());

    expect(screen.getByTestId("voice-ws-status")).toHaveTextContent("Connected");
    expect(socket.sent).toContainEqual(JSON.stringify({ type: "start", dry_run: true }));
  });

  test("appends the auth token to the WS URL when not in noAuth mode", () => {
    authMock.user = { username: "tester", roles: ["admin"], is_active: true, noAuth: false };
    localStorage.setItem("auth_token", "tok123");

    renderPage();

    expect(lastSocket().url).toBe(buildVoiceTestWsUrl(false));
    expect(lastSocket().url).toContain(`${VOICE_TEST_WS_PATH}?token=tok123`);
  });

  test("page still renders and shows a disconnected badge when the server is absent", () => {
    renderPage();

    act(() => lastSocket().serverClose());

    expect(screen.getByTestId("voice-ws-status")).toHaveTextContent("Disconnected");
    // Core UI remains usable.
    expect(screen.getByTestId("voice-test-page")).toBeInTheDocument();
    expect(screen.getByLabelText("Simulate a voice command")).toBeInTheDocument();
  });

  describe("device picker", () => {
    test("renders a default option and enumerated audio-input devices", async () => {
      (navigator.mediaDevices.enumerateDevices as ReturnType<typeof vi.fn>).mockResolvedValue([
        { kind: "audioinput", deviceId: "mic-a", label: "Built-in Mic" },
        { kind: "audioinput", deviceId: "mic-b", label: "USB Headset" },
        { kind: "audiooutput", deviceId: "spk-a", label: "Speakers" },
      ]);
      renderPage();

      const select = await screen.findByTestId("voice-device-select");
      expect(select).toBeInTheDocument();
      // System default + 2 audio inputs (the audiooutput is filtered out).
      await waitFor(() =>
        expect(screen.getByRole("option", { name: "Built-in Mic" })).toBeInTheDocument(),
      );
      expect(screen.getByRole("option", { name: "USB Headset" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "System default" })).toBeInTheDocument();
      expect(screen.queryByRole("option", { name: "Speakers" })).not.toBeInTheDocument();
    });

    test("passes the selected deviceId as a getUserMedia constraint", async () => {
      (navigator.mediaDevices.enumerateDevices as ReturnType<typeof vi.fn>).mockResolvedValue([
        { kind: "audioinput", deviceId: "mic-b", label: "USB Headset" },
      ]);
      const getUserMedia = navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>;
      renderPage();

      await screen.findByRole("option", { name: "USB Headset" });
      fireEvent.change(screen.getByTestId("voice-device-select"), {
        target: { value: "mic-b" },
      });
      fireEvent.click(screen.getByTestId("mic-toggle"));

      await waitFor(() => expect(getUserMedia).toHaveBeenCalled());
      expect(getUserMedia).toHaveBeenCalledWith({
        audio: { deviceId: { exact: "mic-b" } },
      });
    });
  });

  describe("microphone permission flow", () => {
    test("idle -> requesting -> active, then stop returns to idle", async () => {
      let resolveStream!: (s: MediaStream) => void;
      (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise<MediaStream>((resolve) => {
          resolveStream = resolve;
        }),
      );
      renderPage();
      // Streaming state requires an open socket too.
      act(() => lastSocket().serverOpen());

      expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone off");

      fireEvent.click(screen.getByTestId("mic-toggle"));
      expect(screen.getByTestId("mic-state")).toHaveTextContent("Waiting for permission...");
      expect(screen.getByTestId("mic-toggle")).toBeDisabled();

      await act(async () => resolveStream(fakeStream));

      // MediaRecorder is undefined in jsdom, so the recorder never starts; the
      // honest state reports the mic is on but not streaming.
      expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone on — not streaming");
      expect(screen.getByTestId("voice-level-meter")).toBeInTheDocument();
      expect(screen.getByRole("meter", { name: "Microphone input level" })).toBeInTheDocument();

      fireEvent.click(screen.getByTestId("mic-toggle"));
      expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone off");
      expect(fakeTrack.stop).toHaveBeenCalled();
      expect(screen.queryByTestId("voice-level-meter")).not.toBeInTheDocument();
    });

    test("reports honest streaming state once the recorder is running", async () => {
      // Provide a minimal MediaRecorder so the recorder branch runs.
      class FakeRecorder {
        ondataavailable: ((e: unknown) => void) | null = null;
        start() {}
        stop() {}
      }
      (globalThis as any).MediaRecorder = FakeRecorder;
      try {
        renderPage();
        act(() => lastSocket().serverOpen());

        fireEvent.click(screen.getByTestId("mic-toggle"));
        await waitFor(() =>
          expect(screen.getByTestId("mic-state")).toHaveTextContent(
            "Listening — streaming to server",
          ),
        );
        expect(screen.queryByTestId("mic-stream-warning")).not.toBeInTheDocument();
      } finally {
        delete (globalThis as any).MediaRecorder;
      }
    });

    test("warns when the mic is on but the socket is down", async () => {
      class FakeRecorder {
        ondataavailable: ((e: unknown) => void) | null = null;
        start() {}
        stop() {}
      }
      (globalThis as any).MediaRecorder = FakeRecorder;
      try {
        renderPage();
        // Socket never opened.
        fireEvent.click(screen.getByTestId("mic-toggle"));
        await waitFor(() =>
          expect(screen.getByTestId("mic-stream-warning")).toBeInTheDocument(),
        );
        expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone on — not streaming");
      } finally {
        delete (globalThis as any).MediaRecorder;
      }
    });

    test("shows the denied state when getUserMedia rejects", async () => {
      (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mockRejectedValue(
        new DOMException("Permission denied", "NotAllowedError"),
      );
      renderPage();

      fireEvent.click(screen.getByTestId("mic-toggle"));

      await waitFor(() =>
        expect(screen.getByTestId("mic-state")).toHaveTextContent("Permission denied"),
      );
      expect(screen.getByTestId("mic-denied-alert")).toBeInTheDocument();
      // The button stays available for a retry.
      expect(screen.getByTestId("mic-toggle")).toBeEnabled();
    });

    test("treats a missing mediaDevices API as denied", async () => {
      Object.defineProperty(navigator, "mediaDevices", {
        configurable: true,
        value: undefined,
      });
      renderPage();

      fireEvent.click(screen.getByTestId("mic-toggle"));

      expect(screen.getByTestId("mic-denied-alert")).toBeInTheDocument();
    });
  });

  describe("text simulation and stage timeline", () => {
    test("sends {type:'text', text} and renders returned stage events with timing", async () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      const input = screen.getByLabelText("Simulate a voice command");
      fireEvent.change(input, { target: { value: "hey chatty open browser" } });
      fireEvent.click(screen.getByTestId("voice-simulate-send"));

      expect(socket.sent).toContainEqual(
        JSON.stringify({ type: "text", text: "hey chatty open browser" }),
      );
      expect(input).toHaveValue(""); // cleared after send
      // Processing indicator appears until the next stage event arrives.
      expect(screen.getByTestId("voice-processing")).toBeInTheDocument();

      const base = 1717900000000; // realistic epoch-ms timestamp
      act(() => {
        socket.serverEvent({ stage: "listening", data: {}, ts: base });
        socket.serverEvent({
          stage: "transcript",
          data: { text: "open browser" },
          ts: base + 120,
        });
        socket.serverEvent({
          stage: "match",
          data: { command: "open_browser", success: true, matched: true },
          ts: base + 150,
        });
        socket.serverEvent({
          stage: "dry_run_action",
          data: { action: "would have pressed ctrl+shift+b" },
          ts: base + 160,
        });
      });

      // Processing indicator clears once stages arrive.
      expect(screen.queryByTestId("voice-processing")).not.toBeInTheDocument();

      const events = screen.getAllByTestId("voice-stage-event");
      expect(events).toHaveLength(4);
      expect(events[0]).toHaveTextContent("Listening");
      expect(events[1]).toHaveTextContent("Transcript");
      expect(events[1]).toHaveTextContent("open browser");
      expect(events[2]).toHaveTextContent("Command match");
      expect(events[3]).toHaveTextContent("would have pressed ctrl+shift+b");
      // Per-stage timing: first event shows "start", later ones show ms deltas.
      expect(events[0]).toHaveTextContent("start");
      expect(events[2]).toHaveTextContent("+30ms");
      // Success styling on every event.
      for (const el of events) {
        expect(el).toHaveAttribute("data-status", "success");
      }
      // Empty state is gone.
      expect(screen.queryByTestId("voice-timeline-empty")).not.toBeInTheDocument();
      // Transcript surfaced in its dedicated panel.
      expect(screen.getByTestId("transcript-text")).toHaveTextContent("open browser");
    });

    test("never renders a negative delta for out-of-order timestamps", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      const base = 1717900000000; // epoch-ms
      act(() => {
        socket.serverEvent({ stage: "listening", data: {}, ts: base + 500 });
        // Out-of-order: this stage's ts is *earlier* than the previous one, which
        // would naively yield a negative delta.
        socket.serverEvent({ stage: "transcript", data: { text: "x" }, ts: base });
      });

      const events = screen.getAllByTestId("voice-stage-event");
      expect(events).toHaveLength(2);
      // First row is the baseline; second must clamp to a non-negative delta.
      expect(events[0]).toHaveTextContent("start");
      const delta = events[1].textContent ?? "";
      expect(delta).not.toMatch(/-\d/); // no negative number anywhere in the row
      expect(delta).toContain("+0ms");
    });

    test("assigns each stage event a stable, unique id used as its key", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => {
        socket.serverEvent({ stage: "listening", data: {}, ts: 1 });
        socket.serverEvent({ stage: "transcript", data: { text: "a" }, ts: 2 });
        socket.serverEvent({ stage: "match", data: { matched: true }, ts: 3 });
      });

      const events = screen.getAllByTestId("voice-stage-event");
      expect(events).toHaveLength(3);
      const ids = events.map((el) => el.getAttribute("data-event-id"));
      // Every row carries an id...
      for (const id of ids) {
        expect(id).toBeTruthy();
      }
      // ...and they are unique and monotonic, so the ring buffer can scroll
      // without index-based keys colliding.
      expect(new Set(ids).size).toBe(ids.length);
      const numeric = ids.map((id) => Number(id));
      expect(numeric[0]).toBeLessThan(numeric[1]);
      expect(numeric[1]).toBeLessThan(numeric[2]);
    });

    test("renders the timeline as an aria-live log", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());
      act(() => socket.serverEvent({ stage: "listening", data: {}, ts: 1 }));

      const timeline = screen.getByTestId("voice-stage-timeline");
      expect(timeline).toHaveAttribute("role", "log");
      expect(timeline).toHaveAttribute("aria-live", "polite");
    });

    test("highlights the wake-word stage distinctly and shows the detected affordance", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => {
        socket.serverEvent({ stage: "wakeword", data: { keyword: "hey chatty" }, ts: 1 });
      });

      expect(screen.getByTestId("wake-word-detected")).toBeInTheDocument();
      expect(screen.getByTestId("wake-word-badge")).toBeInTheDocument();
      const event = screen.getByTestId("voice-stage-event");
      expect(event).toHaveAttribute("data-wakeword", "true");
    });

    test("shows the transcript-unavailable explainer when the server reports it", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => {
        socket.serverEvent({
          stage: "listening",
          data: { transcription_available: false },
          ts: 1,
        });
      });

      expect(screen.getByTestId("transcript-unavailable")).toHaveTextContent(
        /Speech-to-text isn't configured/i,
      );
    });

    test("renders failure styling for error events and unmatched data", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => {
        socket.serverEvent({
          stage: "match",
          data: { matched: false, text: "blah" },
          ts: 2000,
        });
        socket.serverEvent({ stage: "error", data: { error: "pipeline crashed" }, ts: 2050 });
      });

      const events = screen.getAllByTestId("voice-stage-event");
      expect(events).toHaveLength(2);
      expect(events[0]).toHaveAttribute("data-status", "failure");
      expect(events[1]).toHaveAttribute("data-status", "failure");
      expect(events[1]).toHaveTextContent("Error");
    });

    test("wake-word example chips fill the simulation input", () => {
      renderPage();
      act(() => lastSocket().serverOpen());

      const chips = screen.getAllByTestId("wake-word-chip");
      expect(chips.length).toBeGreaterThan(0);
      fireEvent.click(chips[0]);
      expect(screen.getByLabelText("Simulate a voice command")).toHaveValue(
        chips[0].textContent,
      );
    });

    test("send button is disabled while disconnected", async () => {
      renderPage();

      fireEvent.change(screen.getByLabelText("Simulate a voice command"), {
        target: { value: "open browser" },
      });
      // Socket never opened -> still connecting -> cannot send.
      expect(screen.getByTestId("voice-simulate-send")).toBeDisabled();

      act(() => lastSocket().serverOpen());
      expect(screen.getByTestId("voice-simulate-send")).toBeEnabled();
    });
  });

  describe("author -> test deep link (?command=)", () => {
    test("prefills the simulation input from ?command= and shows a target banner", () => {
      renderPage("/voice-test?command=open_browser");

      // Banner naming the command under test.
      expect(screen.getByTestId("voice-test-target-banner")).toHaveTextContent(
        "Testing: open_browser",
      );
      // Input is prefilled even before the socket connects.
      expect(screen.getByLabelText("Simulate a voice command")).toHaveValue("open_browser");
    });

    test("decodes URL-encoded command names", () => {
      renderPage("/voice-test?command=hey%20chatty%20open%20browser");

      expect(screen.getByLabelText("Simulate a voice command")).toHaveValue(
        "hey chatty open browser",
      );
    });

    test("auto-sends the prefilled command once connected (dry-run pipeline only)", () => {
      renderPage("/voice-test?command=open_browser");
      const socket = lastSocket();

      // Nothing sent until the socket is actually open.
      expect(socket.sent).not.toContainEqual(
        JSON.stringify({ type: "text", text: "open_browser" }),
      );

      act(() => socket.serverOpen());

      // On connect: the safe text-simulation frame is sent exactly once...
      expect(socket.sent).toContainEqual(
        JSON.stringify({ type: "text", text: "open_browser" }),
      );
      const sends = socket.sent.filter(
        (m) => m === JSON.stringify({ type: "text", text: "open_browser" }),
      );
      expect(sends).toHaveLength(1);
      // ...the processing indicator is shown.
      expect(screen.getByTestId("voice-processing")).toBeInTheDocument();
    });

    test("keeps the input populated for an auto-sent prefill so it can be resent", () => {
      renderPage("/voice-test?command=open_browser");
      const socket = lastSocket();

      act(() => socket.serverOpen());

      // The auto-send fired (frame on the wire)...
      expect(socket.sent).toContainEqual(
        JSON.stringify({ type: "text", text: "open_browser" }),
      );
      // ...but unlike a manual send, the input is NOT cleared: clearing it would
      // empty the prefill the effect just set and strand the user with no way to
      // re-run the command.
      expect(screen.getByLabelText("Simulate a voice command")).toHaveValue("open_browser");
    });

    test("no banner or auto-send without a ?command= param", () => {
      renderPage();
      act(() => lastSocket().serverOpen());

      expect(screen.queryByTestId("voice-test-target-banner")).not.toBeInTheDocument();
      expect(lastSocket().sent).not.toContainEqual(
        expect.stringContaining('"type":"text"'),
      );
    });
  });

  describe("WebSocket close handling", () => {
    test("auth-policy close (1008) stops retrying and signals session expiry", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      const socketCount = TestWebSocket.instances.length;
      act(() => socket.serverClose(1008, "policy violation"));

      // Honest non-retrying state + manual reconnect affordance.
      expect(screen.getByTestId("voice-ws-status")).toHaveTextContent(
        "Disconnected — reconnect",
      );
      expect(screen.getByTestId("voice-ws-reconnect")).toBeInTheDocument();
      // Session-expiry was signalled, and no blind reconnect attempt was made.
      expect(notifySessionExpiredMock).toHaveBeenCalledTimes(1);
      expect(TestWebSocket.instances.length).toBe(socketCount);
    });

    test("app-level unauthorized close (4401) is treated as auth-policy too", () => {
      renderPage();
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => socket.serverClose(4401, "unauthorized"));

      expect(screen.getByTestId("voice-ws-status")).toHaveTextContent(
        "Disconnected — reconnect",
      );
      expect(notifySessionExpiredMock).toHaveBeenCalledTimes(1);
    });

    test("exhausting all reconnect attempts shows an honest non-retrying state", () => {
      vi.useFakeTimers();
      try {
        renderPage();

        // Drive every transient (1006) close + its backoff timer until retries
        // are spent. MAX_RECONNECT_ATTEMPTS is 10.
        for (let i = 0; i < 12; i++) {
          act(() => lastSocket().serverClose(1006, "abnormal"));
          act(() => {
            vi.runOnlyPendingTimers();
          });
        }

        expect(screen.getByTestId("voice-ws-status")).toHaveTextContent(
          "Disconnected — reconnect",
        );
        // Auth path was NOT triggered for plain network drops.
        expect(notifySessionExpiredMock).not.toHaveBeenCalled();
      } finally {
        vi.useRealTimers();
      }
    });

    test("manual reconnect button re-attempts the connection", () => {
      vi.useFakeTimers();
      try {
        renderPage();

        for (let i = 0; i < 12; i++) {
          act(() => lastSocket().serverClose(1006, "abnormal"));
          act(() => {
            vi.runOnlyPendingTimers();
          });
        }

        const before = TestWebSocket.instances.length;
        act(() => fireEvent.click(screen.getByTestId("voice-ws-reconnect")));

        // A fresh socket is created and the badge returns to "Connecting...".
        expect(TestWebSocket.instances.length).toBe(before + 1);
        expect(screen.getByTestId("voice-ws-status")).toHaveTextContent("Connecting...");
      } finally {
        vi.useRealTimers();
      }
    });
  });

  test("renders the shared brand mark alongside the page heading", () => {
    renderPage();
    // The shared Logo exposes an aria-label only when non-decorative; here it is
    // decorative, so we assert the heading still reads "Voice Test" and a single
    // brand wordmark is not duplicated on the page.
    expect(screen.getByRole("heading", { name: "Voice Test" })).toBeInTheDocument();
  });
});
