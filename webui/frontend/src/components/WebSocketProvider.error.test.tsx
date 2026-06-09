import React from "react";
import { render, act } from "@testing-library/react";
import { vi, it, beforeEach, afterEach } from "vitest";
import { WebSocketProvider } from "./WebSocketProvider";

// The user object must be referentially stable across renders, because the
// provider's connect effect depends on it.
vi.mock("../hooks/useAuth", () => {
  const user = { username: "tester", is_active: true, roles: ["admin"] };
  return {
    useAuth: () => ({ user, isAuthenticated: true }),
  };
});

class ErrorWS {
  public onopen: any = null;
  public onclose: any = null;
  public onerror: any = null;
  public onmessage: any = null;
  public url: string;
  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onerror && this.onerror(new Error("boom")), 0);
    setTimeout(() => this.onclose && this.onclose({ type: "close" }), 1);
  }
  close() { }
}

beforeEach(() => {
  localStorage.setItem("auth_token", "token");
  // @ts-ignore
  global.WebSocket = ErrorWS;
  vi.useFakeTimers();
});

afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
  localStorage.clear();
});

it("handles websocket error and close without crashing", () => {
  const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });
  const { unmount } = render(
    <WebSocketProvider>
      <div>Child</div>
    </WebSocketProvider>,
  );
  act(() => {
    vi.runOnlyPendingTimers();
  });
  unmount();
  consoleSpy.mockRestore();
});
