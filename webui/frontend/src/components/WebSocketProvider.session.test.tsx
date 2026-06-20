import React from "react";
import { render, act } from "@testing-library/react";
import { vi, it, expect, beforeEach, afterEach } from "vitest";
import { WebSocketProvider, useWebSocket } from "./WebSocketProvider";

// Stable user so the provider's connect effect doesn't re-run spuriously.
vi.mock("../hooks/useAuth", () => {
  const user = { username: "tester", is_active: true, roles: ["admin"] };
  return { useAuth: () => ({ user, isAuthenticated: true }) };
});

// Spy on the shared session-expiry signal the provider calls on auth-close.
const notifySessionExpired = vi.fn();
vi.mock("../services/authService", () => ({
  notifySessionExpired: () => notifySessionExpired(),
}));

// MockWS that does NOT auto-open: this models a server that is down, so every
// reconnect attempt fails to open and the attempt counter is never reset by an
// onopen — which is exactly how reconnection becomes exhausted in practice. The
// initial socket is opened explicitly by the test when a live connection is
// wanted.
class MockWS {
  static instances: MockWS[] = [];
  public onopen: any = null;
  public onclose: any = null;
  public onerror: any = null;
  public onmessage: any = null;
  public url: string;
  constructor(url: string) {
    this.url = url;
    MockWS.instances.push(this);
  }
  close() {
    /* noop */
  }
}

// Test consumer that surfaces the context fields under test.
let captured: ReturnType<typeof useWebSocket> | null = null;
function Probe() {
  captured = useWebSocket();
  return null;
}

beforeEach(() => {
  MockWS.instances = [];
  captured = null;
  notifySessionExpired.mockClear();
  localStorage.setItem("auth_token", "token");
  // @ts-ignore
  global.WebSocket = MockWS;
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  localStorage.clear();
});

it("exposes reconnectExhausted after MAX_RECONNECT_ATTEMPTS are used up", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <Probe />
    </WebSocketProvider>,
  );

  // Open the initial socket.
  act(() => {
    vi.advanceTimersByTime(1);
  });
  expect(captured?.reconnectExhausted).toBe(false);

  // Drive 11 unexpected closes (> the 10 max attempts). Each close schedules a
  // backoff reconnect; advancing time fires it and opens the next socket.
  for (let i = 0; i < 11; i++) {
    const sock = MockWS.instances[MockWS.instances.length - 1];
    act(() => {
      sock.onclose?.({ type: "close", code: 1006, reason: "" });
    });
    act(() => {
      vi.advanceTimersByTime(60000); // exceed the capped 30s backoff
    });
  }

  expect(captured?.reconnectExhausted).toBe(true);
  unmount();
});

it("manual reconnect() clears the exhausted state and reopens", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <Probe />
    </WebSocketProvider>,
  );
  act(() => {
    vi.advanceTimersByTime(1);
  });

  // Exhaust reconnection.
  for (let i = 0; i < 11; i++) {
    const sock = MockWS.instances[MockWS.instances.length - 1];
    act(() => sock.onclose?.({ type: "close", code: 1006, reason: "" }));
    act(() => vi.advanceTimersByTime(60000));
  }
  expect(captured?.reconnectExhausted).toBe(true);

  const before = MockWS.instances.length;
  act(() => {
    captured?.reconnect();
  });

  expect(captured?.reconnectExhausted).toBe(false);
  expect(MockWS.instances.length).toBe(before + 1);

  unmount();
});

it("treats an auth-policy close (1008) as session expiry and stops reconnecting", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <Probe />
    </WebSocketProvider>,
  );
  act(() => {
    vi.advanceTimersByTime(1);
  });

  const sock = MockWS.instances[0];
  act(() => {
    sock.onclose?.({ type: "close", code: 1008, reason: "auth" });
  });

  expect(notifySessionExpired).toHaveBeenCalledTimes(1);

  // No reconnect should be scheduled after an auth close.
  act(() => {
    vi.advanceTimersByTime(60000);
  });
  expect(MockWS.instances.length).toBe(1);

  unmount();
});

it("treats an app-specific 4401 close as session expiry", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <Probe />
    </WebSocketProvider>,
  );
  act(() => {
    vi.advanceTimersByTime(1);
  });

  act(() => {
    MockWS.instances[0].onclose?.({ type: "close", code: 4401, reason: "" });
  });

  expect(notifySessionExpired).toHaveBeenCalledTimes(1);
  unmount();
});
