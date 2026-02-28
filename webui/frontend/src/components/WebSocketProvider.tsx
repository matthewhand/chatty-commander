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
    if (!isAuthenticated) return;

    const token = localStorage.getItem("auth_token");
    // Only require token if we are not in no-auth mode. Since we don't have that info easily,
    // let's pass token if it exists, otherwise pass empty token
    const tokenQuery = token ? `?token=${token}` : "";

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Construct websocket URL using the current host, but respect an env var if provided during build
    // Or if in dev mode (Vite typically runs on 5173), fallback to the standard backend port 8100
    const host = window.location.port === "5173" || window.location.port === "3000"
      ? window.location.hostname + ":8100"
      : window.location.host;
    const socket = new WebSocket(`${protocol}//${host}/ws${tokenQuery}`);

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
