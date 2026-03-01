import React from "react";
import { render, act } from "@testing-library/react";
import { WebSocketProvider } from "./WebSocketProvider";
import { vi, it } from 'vitest';

vi.useFakeTimers();

// Mock useAuth to authenticate
vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

// Mock localStorage for token
Object.defineProperty(window, "localStorage", {
  value: {
    getItem: (k: string) => (k === "auth_token" ? "token" : null),
  },
});

class MockWS {
  public onopen: any = null;
  public onclose: any = null;
  public onerror: any = null;
  public url: string;
  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onopen && this.onopen({ type: "open" }), 0);
    setTimeout(() => this.onclose && this.onclose({ type: "close" }), 5);
  }
  close() {
    /* noop */
  }
}

// @ts-ignore
global.WebSocket = MockWS;

it("connects and then closes (reconnect handled by component lifecycle)", () => {
  const { unmount } = render(
    <WebSocketProvider>
      <div>Child</div>
    </WebSocketProvider>,
  );
  act(() => {
    vi.advanceTimersByTime(100);
  });
  unmount();
});
