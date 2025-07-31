import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for WebSocket connection management
 * Provides automatic reconnection, connection status, and message handling
 */
export const useWebSocket = (url, options = {}) => {
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onOpen = null,
    onClose = null,
    onError = null,
    onMessage = null,
    protocols = []
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [error, setError] = useState(null);

  const ws = useRef(null);
  const reconnectTimeoutId = useRef(null);
  const shouldReconnect = useRef(true);

  // Clear reconnection timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutId.current) {
      clearTimeout(reconnectTimeoutId.current);
      reconnectTimeoutId.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      setError(null);
      
      // Close existing connection if any
      if (ws.current) {
        ws.current.close();
      }

      // Create new WebSocket connection
      ws.current = new WebSocket(url, protocols);

      ws.current.onopen = (event) => {
        console.log('WebSocket connected:', url);
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        setError(null);
        
        if (onOpen) {
          onOpen(event);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event?.code ?? 1000, event?.reason ?? '');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        if (onClose) {
          onClose(event);
        }

        // Attempt to reconnect if not manually closed
        if (shouldReconnect.current && reconnectAttempts < maxReconnectAttempts) {
          setConnectionStatus('reconnecting');
          setReconnectAttempts(prev => prev + 1);
          
          reconnectTimeoutId.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setConnectionStatus('failed');
          setError('Maximum reconnection attempts reached');
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setConnectionStatus('error');
        
        if (onError) {
          onError(event);
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message = {
            data: event.data,
            timestamp: new Date().toISOString(),
            type: 'message'
          };
          
          setLastMessage(message);
          
          if (onMessage) {
            onMessage(message);
          }
        } catch (err) {
          console.error('Error processing WebSocket message:', err);
          setError('Error processing message');
        }
      };

    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
      setConnectionStatus('error');
    }
  }, [url, protocols, onOpen, onClose, onError, onMessage, reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  // Send message through WebSocket
  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        const messageToSend = typeof message === 'string' ? message : JSON.stringify(message);
        ws.current.send(messageToSend);
        return true;
      } catch (err) {
        console.error('Error sending WebSocket message:', err);
        setError('Failed to send message');
        return false;
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
      setError('WebSocket not connected');
      return false;
    }
  }, []);

  // Manually disconnect
  const disconnect = useCallback(() => {
    shouldReconnect.current = false;
    clearReconnectTimeout();
    
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, [clearReconnectTimeout]);

  // Manually reconnect
  const reconnect = useCallback(() => {
    shouldReconnect.current = true;
    setReconnectAttempts(0);
    clearReconnectTimeout();
    connect();
  }, [connect, clearReconnectTimeout]);

  // Get connection ready state
  const getReadyState = useCallback(() => {
    if (!ws.current) return WebSocket.CLOSED;
    return ws.current.readyState;
  }, []);

  // Get ready state as string
  const getReadyStateString = useCallback(() => {
    const readyState = getReadyState();
    switch (readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }, [getReadyState]);

  // Initialize connection on mount
  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    // Cleanup on unmount
    return () => {
      shouldReconnect.current = false;
      clearReconnectTimeout();
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect, clearReconnectTimeout]);

  // Cleanup effect for reconnection timeout
  useEffect(() => {
    return () => {
      clearReconnectTimeout();
    };
  }, [clearReconnectTimeout]);

  return {
    // Connection state
    isConnected,
    connectionStatus,
    reconnectAttempts,
    error,
    
    // Message handling
    lastMessage,
    sendMessage,
    
    // Connection control
    connect,
    disconnect,
    reconnect,
    
    // Connection info
    getReadyState,
    getReadyStateString,
    
    // WebSocket instance (for advanced usage)
    webSocket: ws.current
  };
};

export default useWebSocket;