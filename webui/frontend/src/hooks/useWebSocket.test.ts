import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";

class MockWS {
  onopen: any;
  onclose: any;
  onerror: any;
  onmessage: any;
  readyState: number = 0;
  sent: any[] = [];
  
  constructor(public url: string) {
    this.readyState = 0;
    MockWS.instances.push(this);
  }
  
  send(data: any) { this.sent.push(data); }
  close(code = 1000, reason = "") { 
    this.readyState = 3; 
    if (this.onclose) this.onclose({ code, reason });
  }
  
  static instances: MockWS[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
}

(MockWS as any).CONNECTING = 0;
(MockWS as any).OPEN = 1;
(MockWS as any).CLOSING = 2;
(MockWS as any).CLOSED = 3;

const originalWS = global.WebSocket;

beforeEach(() => {
  MockWS.instances = [];
  global.WebSocket = MockWS as any;
});

afterEach(() => {
  global.WebSocket = originalWS;
  vi.restoreAllMocks();
});

describe("useWebSocket", () => {
  test("lifecycle", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test", { autoReconnect: false }));
    const ws = MockWS.instances[0];
    act(() => { ws.readyState = 1; ws.onopen({ type: "open" }); });
    expect(result.current.isConnected).toBe(true);
    act(() => { ws.onmessage({ data: "msg" }); });
    expect(result.current.lastMessage?.data).toBe("msg");
    act(() => { result.current.sendMessage("out"); });
    expect(ws.sent).toContain("out");
    act(() => { result.current.disconnect(); });
    expect(result.current.isConnected).toBe(false);
  });

  test("auto reconnect", async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useWebSocket("ws://test", { reconnectInterval: 100 }));
    const ws1 = MockWS.instances[0];
    act(() => { ws1.onclose({ code: 1006 }); });
    expect(result.current.connectionStatus).toBe("reconnecting");
    act(() => { vi.advanceTimersByTime(100); });
    expect(MockWS.instances.length).toBe(2);
    vi.useRealTimers();
  });

  test("manual reconnect", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test", { autoReconnect: false }));
    act(() => { result.current.reconnect(); });
    expect(MockWS.instances.length).toBe(2);
  });

  test("getReadyState", async () => {
    const { result } = renderHook(() => useWebSocket("ws://test", { autoReconnect: false }));
    expect(result.current.getReadyState()).toBe(0);
    act(() => { MockWS.instances[0].readyState = 1; });
    expect(result.current.getReadyState()).toBe(1);
  });
});
