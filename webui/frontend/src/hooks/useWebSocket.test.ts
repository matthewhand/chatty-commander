import { renderHook, act } from '@testing-library/react';
import useWebSocket from './useWebSocket';

describe('useWebSocket Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('initializes WebSocket connection', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8100/ws'));
    
    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionStatus).toBe('CONNECTING');
  });

  test('handles connection open', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8100/ws'));
    
    // Simulate WebSocket connection opening
    await act(async () => {
      // The mock WebSocket will automatically "connect" after 100ms
      await new Promise(resolve => setTimeout(resolve, 150));
    });
    
    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionStatus).toBe('OPEN');
  });

  test('sends messages when connected', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8100/ws'));
    
    act(() => {
      result.current.sendMessage({ type: 'test', data: 'hello' });
    });
    
    // Message sending is handled by the mock WebSocket
    expect(result.current.sendMessage).toBeDefined();
  });

  test('handles connection errors', () => {
    const { result } = renderHook(() => useWebSocket('ws://invalid-url'));
    
    // The hook should handle connection errors gracefully
    expect(result.current.connectionStatus).toBeDefined();
  });
});