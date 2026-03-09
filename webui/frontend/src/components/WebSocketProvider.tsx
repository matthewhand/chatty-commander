import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "../hooks/useAuth";

type WebSocketContextType = {
  ws: WebSocket | null;
  isConnected: boolean;
  reconnectAttempt: number;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(
  undefined,
);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { user } = useAuth();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  // Refs to manage reconnection timer and state without triggering re-renders
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptRef = useRef(0);
  const shouldReconnectRef = useRef(true);
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 second

  const connect = useCallback(() => {
    if (!user) return;

    // Use current location to determine WebSocket URL dynamically
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    let wsUrl = `${protocol}//${host}/ws`;

    // Only append token if available and NOT explicitly marked as noAuth.
    const token = localStorage.getItem("auth_token");
    if (token && !user.noAuth) {
      wsUrl += `?token=${token}`;
    }

    console.log(`WebSocketProvider: Connecting to ${wsUrl} (Attempt ${reconnectAttemptRef.current})`);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("WebSocketProvider: Connected");
      setIsConnected(true);
      reconnectAttemptRef.current = 0;
      setReconnectAttempt(0); // Sync display state
    };

    socket.onclose = (ev) => {
      console.log("WebSocketProvider: Disconnected", ev.code, ev.reason);
      setIsConnected(false);
      setWs(null);

      if (!shouldReconnectRef.current) return;

      if (reconnectAttemptRef.current < maxReconnectAttempts) {
        const attempt = reconnectAttemptRef.current;
        const delay = Math.min(30000, baseReconnectDelay * Math.pow(1.5, attempt));
        console.log(`WebSocketProvider: Reconnecting in ${delay}ms...`);

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptRef.current += 1;
          setReconnectAttempt(reconnectAttemptRef.current); // Update display
          connect();
        }, delay);
      } else {
        console.error("WebSocketProvider: Max reconnect attempts reached");
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocketProvider: Error", error);
    };

    setWs(socket);
  }, [user]); // Only depends on user — reconnect logic uses refs, not state

  useEffect(() => {
    if (!user) return;

    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    connect();

    return () => {
      console.log("WebSocketProvider: Cleanup/Closing socket");
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      setWs((current) => {
        if (current) {
          current.onclose = null; // Prevent reconnect on intentional close
          current.close();
        }
        return null;
      });
    };
  }, [user, connect]); // Only re-run when user changes, not on every reconnect attempt

  return (
    <WebSocketContext.Provider value={{ ws, isConnected, reconnectAttempt }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within WebSocketProvider");
  }
  return context;
};
