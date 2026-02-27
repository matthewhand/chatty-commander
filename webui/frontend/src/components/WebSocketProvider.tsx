import React, { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";

type WebSocketContextType = {
  ws: WebSocket | null;
  isConnected: boolean;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(
  undefined,
);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { isAuthenticated } = useAuth();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  useEffect(() => {
    // If we're authenticated, or if we're in no-auth mode (isAuthenticated is true but no token)
    if (!isAuthenticated) return;

    const token = localStorage.getItem("auth_token");

    // Dynamic WebSocket URL resolution
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host; // includes port
    let wsUrl = `${protocol}//${host}/ws`;

    if (token) {
      wsUrl += `?token=${token}`;
    }

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => setIsConnected(true);
    socket.onclose = () => setIsConnected(false);
    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [isAuthenticated]);

  return (
    <WebSocketContext.Provider value={{ ws, isConnected }}>
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
