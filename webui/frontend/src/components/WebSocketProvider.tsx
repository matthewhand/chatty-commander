import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifySessionExpired } from "../services/authService";
import { logger } from "../utils/logger";

type WebSocketContextType = {
  ws: WebSocket | null;
  isConnected: boolean;
  reconnectAttempt: number;
  lastMessageTime: number | null;
  /**
   * True once automatic reconnection has been exhausted (all
   * MAX_RECONNECT_ATTEMPTS used up) so the UI can offer a manual
   * "connection lost — reconnect" affordance instead of silently giving up.
   */
  reconnectExhausted: boolean;
  /**
   * Manually restart the reconnection cycle from scratch. Intended for a
   * user-facing "Reconnect" button once {@link reconnectExhausted} is true; a
   * no-op while there is no authenticated user.
   */
  reconnect: () => void;
};

/**
 * WebSocket close codes that mean "you are not (or no longer) authorised":
 *  - 1008: policy violation (the standard code servers use to reject auth).
 *  - 4401: app-specific convention mirroring HTTP 401 in the 4000–4999 range.
 * A close with either code is treated as a session expiry, not a transient
 * network drop, so we stop futile reconnects and route through the shared
 * sign-out flow.
 */
const AUTH_CLOSE_CODES = new Set([1008, 4401]);

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
  const [lastMessageTime, setLastMessageTime] = useState<number | null>(null);
  const [reconnectExhausted, setReconnectExhausted] = useState(false);

  // Refs to manage reconnection timer and state without triggering re-renders
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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

    logger.info(`WebSocketProvider: Connecting to ${wsUrl} (Attempt ${reconnectAttemptRef.current})`);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      logger.info("WebSocketProvider: Connected");
      setIsConnected(true);
      reconnectAttemptRef.current = 0;
      setReconnectAttempt(0); // Sync display state
      setReconnectExhausted(false); // A live connection clears any prior "give up" state
    };

    socket.onclose = (ev) => {
      logger.info("WebSocketProvider: Disconnected", ev.code, ev.reason);
      setIsConnected(false);
      setWs(null);

      // An auth-policy close means the session is no longer valid: don't burn
      // reconnect attempts against a server that will keep rejecting us — route
      // through the shared session-expiry flow (clears token, redirects to
      // login). notifySessionExpired no-ops when there's no stored token, so the
      // dev/no-auth flow is unaffected.
      if (AUTH_CLOSE_CODES.has(ev.code)) {
        logger.error(
          `WebSocketProvider: Auth-related close (code ${ev.code}); treating as session expiry`,
        );
        shouldReconnectRef.current = false;
        notifySessionExpired();
        return;
      }

      if (!shouldReconnectRef.current) return;

      if (reconnectAttemptRef.current < maxReconnectAttempts) {
        const attempt = reconnectAttemptRef.current;
        const delay = Math.min(30000, baseReconnectDelay * Math.pow(1.5, attempt));
        logger.debug(`WebSocketProvider: Reconnecting in ${delay}ms...`);

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptRef.current += 1;
          setReconnectAttempt(reconnectAttemptRef.current); // Update display
          connect();
        }, delay);
      } else {
        logger.error("WebSocketProvider: Max reconnect attempts reached");
        // Surface the give-up so consumers can render a manual reconnect prompt
        // instead of the connection silently staying dead.
        setReconnectExhausted(true);
      }
    };

    socket.onmessage = (event) => {
      // Only treat non-empty data frames as activity. Empty frames / keep-alives
      // should not advance lastMessageTime, which the dashboard uses for UI state.
      const data = event.data;
      const isEmpty =
        data == null ||
        (typeof data === "string" && data.trim() === "");
      if (!isEmpty) {
        setLastMessageTime(Date.now());
      }
    };

    socket.onerror = (error) => {
      logger.error("WebSocketProvider: Error", error);
    };

    setWs(socket);
  }, [user]); // Only depends on user — reconnect logic uses refs, not state

  // Manual reconnect: reset the backoff counters and start a fresh cycle. Safe
  // to call at any time; consumers use it for a "Reconnect" button once
  // automatic attempts are exhausted.
  const reconnect = useCallback(() => {
    if (!user) return;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    setReconnectAttempt(0);
    setReconnectExhausted(false);
    connect();
  }, [user, connect]);

  useEffect(() => {
    if (!user) return;

    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    setReconnectExhausted(false);
    connect();

    return () => {
      logger.debug("WebSocketProvider: Cleanup/Closing socket");
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
    <WebSocketContext.Provider
      value={{
        ws,
        isConnected,
        reconnectAttempt,
        lastMessageTime,
        reconnectExhausted,
        reconnect,
      }}
    >
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
