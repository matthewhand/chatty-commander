import { useState, useEffect, useRef, useCallback } from "react";

export interface WebSocketMessage {
  data: string | ArrayBuffer | Blob;
  timestamp: string;
  type: "message";
}

export interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  protocols?: string | string[];
  autoReconnect?: boolean;
  initialStatus?: "CONNECTING" | "OPEN" | "CLOSING" | "CLOSED" | "reconnecting" | "failed" | "error";
}

/**
 * Custom hook for WebSocket connection management
 */
export const useWebSocket = (url: string, options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [connectionStatus, setConnectionStatus] = useState<string>(options.initialStatus || "CONNECTING");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutId = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnect = useRef<boolean>(true);
  
  // Use refs for callbacks/options to avoid effect dependency churn
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (!url) return;

    try {
      setConnectionStatus("CONNECTING");
      
      if (ws.current) {
        ws.current.close();
      }

      ws.current = new WebSocket(url, optionsRef.current.protocols || []);

      ws.current.onopen = (event: Event) => {
        if (import.meta.env.DEV) console.info("WebSocket connected:", url);
        setIsConnected(true);
        setConnectionStatus("OPEN");
        setReconnectAttempts(0);
        setError(null);
        if (optionsRef.current.onOpen) optionsRef.current.onOpen(event);
      };

      ws.current.onclose = (event: CloseEvent) => {
        setIsConnected(false);
        setConnectionStatus("CLOSED");
        if (optionsRef.current.onClose) optionsRef.current.onClose(event);

        if (
          optionsRef.current.autoReconnect !== false &&
          shouldReconnect.current &&
          reconnectAttempts < (optionsRef.current.maxReconnectAttempts ?? 10)
        ) {
          setConnectionStatus("reconnecting");
          setReconnectAttempts((prev) => prev + 1);
          
          reconnectTimeoutId.current = setTimeout(() => {
            connect();
          }, optionsRef.current.reconnectInterval ?? 3000);
        } else if (reconnectAttempts >= (optionsRef.current.maxReconnectAttempts ?? 10)) {
          setConnectionStatus("failed");
          setError("Maximum reconnection attempts reached");
        }
      };

      ws.current.onerror = (event: Event) => {
        if (import.meta.env.DEV) console.error("WebSocket error:", event);
        setError("WebSocket connection error");
        setConnectionStatus("error");
        if (optionsRef.current.onError) optionsRef.current.onError(event);
      };

      ws.current.onmessage = (event: MessageEvent) => {
        const message: WebSocketMessage = {
          data: event.data,
          timestamp: new Date().toISOString(),
          type: "message",
        };
        setLastMessage(message);
        if (optionsRef.current.onMessage) optionsRef.current.onMessage(message);
      };
    } catch (err) {
      setError("Failed to create WebSocket connection");
      setConnectionStatus("error");
    }
  }, [url, reconnectAttempts]); // reconnectAttempts included to trigger effect-based reconnect

  const sendMessage = useCallback((message: string | object) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(typeof message === "string" ? message : JSON.stringify(message));
        return true;
      } catch (err) {
        return false;
      }
    }
    return false;
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnect.current = false;
    if (reconnectTimeoutId.current) clearTimeout(reconnectTimeoutId.current);
    if (ws.current) ws.current.close(1000, "Manual disconnect");
  }, []);

  const reconnect = useCallback(() => {
    shouldReconnect.current = true;
    setReconnectAttempts(0);
    connect();
  }, [connect]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimeoutId.current) clearTimeout(reconnectTimeoutId.current);
      if (ws.current) ws.current.close(1000, "Unmount");
    };
  }, [url]); // Only reconnect if URL changes

  return {
    isConnected,
    connectionStatus,
    reconnectAttempts,
    error,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect,
    getReadyState: () => ws.current?.readyState ?? WebSocket.CLOSED,
  };
};
