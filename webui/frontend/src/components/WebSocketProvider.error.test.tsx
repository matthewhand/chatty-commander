import React from 'react';
import { render } from '@testing-library/react';
import { WebSocketProvider } from './WebSocketProvider';

jest.useFakeTimers();

jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true })
}));

Object.defineProperty(window, 'localStorage', {
  value: { getItem: (k: string) => (k === 'auth_token' ? 'token' : null) }
});

class ErrorWS {
  public onopen: any = null;
  public onclose: any = null;
  public onerror: any = null;
  public url: string;
  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onerror && this.onerror(new Error('boom')), 0);
    setTimeout(() => this.onclose && this.onclose({ type: 'close' }), 1);
  }
  close() {}
}
// @ts-ignore
global.WebSocket = ErrorWS;

it('handles websocket error and close without crashing', () => {
  const { unmount } = render(
    <WebSocketProvider>
      <div>Child</div>
    </WebSocketProvider>
  );
  jest.runOnlyPendingTimers();
  unmount();
});
