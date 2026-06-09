// Vitest setup: registers jest-dom matchers and stubs browser APIs that
// jsdom does not implement (or that we never want hitting the network).
import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// Mock window.matchMedia (used by responsive components / theme detection)
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// ResizeObserver is required by recharts' ResponsiveContainer
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserverMock;

// Default WebSocket mock so components never open real connections in tests.
// Individual tests can (and do) replace global.WebSocket with their own mock.
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState = MockWebSocket.CONNECTING;
  onopen: ((ev?: unknown) => void) | null = null;
  onclose: ((ev?: unknown) => void) | null = null;
  onmessage: ((ev?: unknown) => void) | null = null;
  onerror: ((ev?: unknown) => void) | null = null;

  private listeners: Record<string, Array<(ev?: unknown) => void>> = {};

  constructor(url: string) {
    this.url = url;
  }

  addEventListener(type: string, handler: (ev?: unknown) => void) {
    (this.listeners[type] ||= []).push(handler);
  }

  removeEventListener(type: string, handler: (ev?: unknown) => void) {
    this.listeners[type] = (this.listeners[type] || []).filter(
      (h) => h !== handler,
    );
  }

  send(_data: unknown) {
    // noop
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ type: "close", code: 1000, reason: "" });
  }
}
(globalThis as any).WebSocket = MockWebSocket;
