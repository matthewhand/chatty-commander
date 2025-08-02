import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

type WSHandler = ((ev?: any) => void) | null;

// Deterministic MockWebSocket with explicit control over events and URL filtering
class ControlledWebSocket {
  public url: string;
  public readyState: number = 0; // CONNECTING
  public onopen: WSHandler = null;
  public onmessage: WSHandler = null;
  public onclose: WSHandler = null;
  public onerror: WSHandler = null;
  public sent: any[] = [];

  static instances: ControlledWebSocket[] = [];

  constructor(url: string) {
    this.url = url;
    ControlledWebSocket.instances.push(this);
  }

  triggerOpen() {
    this.readyState = 1; // OPEN
    this.onopen && this.onopen({ type: 'open' });
  }

  triggerError(err: any = new Error('boom')) {
    // Do not auto-close on error
    this.onerror && this.onerror(err);
  }

  triggerClose(code = 1000, reason = 'Component unmounting') {
    this.readyState = 3; // CLOSED
    this.onclose && this.onclose({ code, reason, type: 'close' });
  }

  triggerMessage(data: any) {
    this.onmessage && this.onmessage({ data, type: 'message' });
  }

  send(data: any) {
    if (this.readyState !== 1) throw new Error('WebSocket not open');
    this.sent.push(data);
    Promise.resolve().then(() => this.onmessage && this.onmessage({ data, type: 'message' }));
  }

  close(code?: number, reason?: string) {
    if (this.readyState === 3) return;
    this.triggerClose(code, reason);
  }

  static reset() {
    ControlledWebSocket.instances.length = 0;
  }
}

// Preserve original
const RealWebSocket = (global as any).WebSocket;

// Helper to install/uninstall the mock safely with URL-based behavior
function installWSMock() {
  ControlledWebSocket.reset();
  // @ts-ignore
  (global as any).WebSocket = jest.fn().mockImplementation((url: string) => {
    const ws = new ControlledWebSocket(url);
    // Auto-behavior based on URL to remove manual timing races (schedule on next tick):
    // - ws://test-open and ws://test-send should OPEN automatically on next tick
    // - ws://test-error should emit ERROR automatically on next tick
    setTimeout(() => {
      if (url.includes('test-open') || url.includes('test-send')) {
        // Ensure the instance is still in CONNECTING before opening
        if (ws.readyState === 0) ws.triggerOpen();
      } else if (url.includes('test-error')) {
        // Emit error, then close
        ws.triggerError(new Error('boom'));
        ws.triggerClose(1006, 'test error');
      }
    }, 0);
    return ws;
  });
}
function uninstallWSMock() {
  (global as any).WebSocket = RealWebSocket as any;
  ControlledWebSocket.reset();
}

beforeEach(() => {
  installWSMock();
  // Use fake timers so we can deterministically advance the macrotask tick used by the mock
  jest.useFakeTimers();
});

afterEach(() => {
  // Ensure no pending timers leak across tests
  try {
    jest.runOnlyPendingTimers();
  } catch {}
  uninstallWSMock();
  jest.useRealTimers();
  jest.restoreAllMocks();
});

describe('useWebSocket Hook', () => {
  test('handles connection open', async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket('ws://test-open', { autoReconnect: false, initialStatus: 'CONNECTING' })
    );

    // Drive scheduled macrotask for auto-open
    act(() => {
      jest.runOnlyPendingTimers();
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('OPEN');
    }, { timeout: 2000 });
    expect(result.current.isConnected).toBe(true);

    unmount();
  });

  test('sends messages when connected', async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket('ws://test-send', { autoReconnect: false, initialStatus: 'CONNECTING' })
    );

    // Drive scheduled macrotask for auto-open before asserting
    act(() => {
      jest.runOnlyPendingTimers();
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('OPEN');
    }, { timeout: 2000 });

    // Flush any additional pending timers/macrotasks before sending
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Send only if connected
    act(() => {
      if (result.current.isConnected) {
        result.current.sendMessage({ type: 'PING' });
      }
    });

    // Ensure our mock captured the send
    await waitFor(() => {
      const ws = ControlledWebSocket.instances.find(i => i.url.includes('test-send'));
      expect(ws && ws.sent.length).toBeGreaterThan(0);
    }, { timeout: 2000 });

    unmount();
  });

  test('handles connection errors', async () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result, unmount } = renderHook(() =>
      useWebSocket('ws://test-error', { autoReconnect: false, initialStatus: 'CONNECTING' })
    );

    // Run the scheduled error tick (onerror then onclose)
    act(() => {
      jest.runOnlyPendingTimers();
    });

    await waitFor(() => {
      expect(['error', 'CLOSED']).toContain(result.current.connectionStatus);
    }, { timeout: 2000 });

    // Assert we recorded an error object/message in the hook
    expect(result.current.error).toBeTruthy();

    unmount();
    spy.mockRestore();
  });
});