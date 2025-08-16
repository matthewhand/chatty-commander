import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';

type WebSocketContextType = {
  ws: WebSocket | null;
  isConnected: boolean;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;

    const token = localStorage.getItem('auth_token');
    if (!token) return;

    const socket = new WebSocket(`ws://localhost:8001/ws?token=${token}`);

    socket.onopen = () => setIsConnected(true);
    socket.onclose = () => setIsConnected(false);
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionError('Connection error');
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
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};
