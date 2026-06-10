import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import VoiceTestPage, {
  VOICE_TEST_WS_PATH,
  buildVoiceTestWsUrl,
} from "./VoiceTestPage";

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

  serverClose() {
    this.readyState = TestWebSocket.CLOSED;
    this.onclose?.({ code: 1006, reason: "abnormal" });
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
  // jsdom has no mediaDevices; install a stub per test.
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia: vi.fn().mockResolvedValue(fakeStream) },
  });
});

describe("VoiceTestPage", () => {
  test("renders heading, dry-run banner, and timeline empty state", () => {
    render(<VoiceTestPage />);

    expect(screen.getByRole("heading", { name: "Voice Test" })).toBeInTheDocument();
    expect(
      screen.getByText("Dry-run mode: detected commands are reported, not executed."),
    ).toBeInTheDocument();
    expect(screen.getByTestId("voice-timeline-empty")).toBeInTheDocument();
    expect(screen.getByText("No pipeline events yet.")).toBeInTheDocument();
    expect(document.title).toBe("Voice Test | ChattyCommander");
  });

  test("connects to the voice-test WS path and sends the dry-run start frame", () => {
    render(<VoiceTestPage />);

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

    render(<VoiceTestPage />);

    expect(lastSocket().url).toBe(buildVoiceTestWsUrl(false));
    expect(lastSocket().url).toContain(`${VOICE_TEST_WS_PATH}?token=tok123`);
  });

  test("page still renders and shows a disconnected badge when the server is absent", () => {
    render(<VoiceTestPage />);

    act(() => lastSocket().serverClose());

    expect(screen.getByTestId("voice-ws-status")).toHaveTextContent("Disconnected");
    // Core UI remains usable.
    expect(screen.getByTestId("voice-test-page")).toBeInTheDocument();
    expect(screen.getByLabelText("Simulate a voice command")).toBeInTheDocument();
  });

  describe("microphone permission flow", () => {
    test("idle -> requesting -> active, then stop returns to idle", async () => {
      let resolveStream!: (s: MediaStream) => void;
      (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise<MediaStream>((resolve) => {
          resolveStream = resolve;
        }),
      );
      render(<VoiceTestPage />);

      expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone off");

      fireEvent.click(screen.getByTestId("mic-toggle"));
      expect(screen.getByTestId("mic-state")).toHaveTextContent("Waiting for permission...");
      expect(screen.getByTestId("mic-toggle")).toBeDisabled();

      await act(async () => resolveStream(fakeStream));

      expect(screen.getByTestId("mic-state")).toHaveTextContent(
        "Listening — audio is streaming to the server",
      );
      expect(screen.getByTestId("voice-level-meter")).toBeInTheDocument();
      expect(screen.getByRole("meter", { name: "Microphone input level" })).toBeInTheDocument();

      fireEvent.click(screen.getByTestId("mic-toggle"));
      expect(screen.getByTestId("mic-state")).toHaveTextContent("Microphone off");
      expect(fakeTrack.stop).toHaveBeenCalled();
      expect(screen.queryByTestId("voice-level-meter")).not.toBeInTheDocument();
    });

    test("shows the denied state when getUserMedia rejects", async () => {
      (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mockRejectedValue(
        new DOMException("Permission denied", "NotAllowedError"),
      );
      render(<VoiceTestPage />);

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
      render(<VoiceTestPage />);

      fireEvent.click(screen.getByTestId("mic-toggle"));

      expect(screen.getByTestId("mic-denied-alert")).toBeInTheDocument();
    });
  });

  describe("text simulation and stage timeline", () => {
    test("sends {type:'text', text} and renders returned stage events with timing", async () => {
      render(<VoiceTestPage />);
      const socket = lastSocket();
      act(() => socket.serverOpen());

      const input = screen.getByLabelText("Simulate a voice command");
      fireEvent.change(input, { target: { value: "hey chatty open browser" } });
      fireEvent.click(screen.getByTestId("voice-simulate-send"));

      expect(socket.sent).toContainEqual(
        JSON.stringify({ type: "text", text: "hey chatty open browser" }),
      );
      expect(input).toHaveValue(""); // cleared after send

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
          data: { command: "open_browser", success: true },
          ts: base + 150,
        });
        socket.serverEvent({
          stage: "dry_run_action",
          data: { action: "would have pressed ctrl+shift+b" },
          ts: base + 160,
        });
      });

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
    });

    test("renders failure styling for error events and success:false data", () => {
      render(<VoiceTestPage />);
      const socket = lastSocket();
      act(() => socket.serverOpen());

      act(() => {
        socket.serverEvent({
          stage: "match",
          data: { success: false, error: "no command matched" },
          ts: 2000,
        });
        socket.serverEvent({ stage: "error", data: { error: "pipeline crashed" }, ts: 2050 });
      });

      const events = screen.getAllByTestId("voice-stage-event");
      expect(events).toHaveLength(2);
      expect(events[0]).toHaveAttribute("data-status", "failure");
      expect(events[0]).toHaveTextContent("no command matched");
      expect(events[1]).toHaveAttribute("data-status", "failure");
      expect(events[1]).toHaveTextContent("Error");
    });

    test("send button is disabled while disconnected", async () => {
      render(<VoiceTestPage />);

      fireEvent.change(screen.getByLabelText("Simulate a voice command"), {
        target: { value: "open browser" },
      });
      // Socket never opened -> still connecting -> cannot send.
      expect(screen.getByTestId("voice-simulate-send")).toBeDisabled();

      act(() => lastSocket().serverOpen());
      expect(screen.getByTestId("voice-simulate-send")).toBeEnabled();
    });
  });
});
