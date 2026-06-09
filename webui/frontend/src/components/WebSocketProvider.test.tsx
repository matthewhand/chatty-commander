import React from "react";
import { render, act, screen } from "@testing-library/react";
import { vi, it, expect, beforeEach, afterEach } from "vitest";
import { WebSocketProvider } from "./WebSocketProvider";

// Mock useAuth: the provider connects only when a user object is present.
// The user object must be referentially stable across renders, because the
// provider's connect effect depends on it.
vi.mock("../hooks/useAuth", () => {
  const user = { username: "tester", is_active: true, roles: ["admin"] };
  return {
    useAuth: () => ({ user, isAuthenticated: true }),
  };
});

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
    setTimeout(() => this.onopen && this.onopen({ type: "open" }), 0);
  }
  close() {
    /* noop */
  }
}

beforeEach(() => {
  MockWS.instances = [];
  localStorage.setItem("auth_token", "token");
  // @ts-ignore
  global.WebSocket = MockWS;
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  localStorage.clear();
});

it("connects with the auth token and renders children", () => {
  render(
    <WebSocketProvider>
      <div>Child</div>
    </WebSocketProvider>,
  );

  expect(screen.getByText("Child")).toBeInTheDocument();
  expect(MockWS.instances).toHaveLength(1);
  expect(MockWS.instances[0].url).toContain("/ws");
  expect(MockWS.instances[0].url).toContain("token=token");

  act(() => {
    vi.advanceTimersByTime(100);
  });
});

it("schedules a reconnect when the socket closes unexpectedly", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <div>Child</div>
    </WebSocketProvider>,
  );

  // Open, then simulate an unexpected close.
  act(() => {
    vi.advanceTimersByTime(10);
  });
  act(() => {
    MockWS.instances[0].onclose?.({ type: "close", code: 1006, reason: "" });
  });

  // Reconnect is scheduled with ~1s base delay.
  act(() => {
    vi.advanceTimersByTime(1500);
  });
  expect(MockWS.instances.length).toBeGreaterThanOrEqual(2);

  unmount();
});
