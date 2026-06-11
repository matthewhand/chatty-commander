import React, { useState, useEffect, createContext, useContext, useRef, useCallback } from "react";
import { authService, User } from "../services/authService";
import { logger } from "../utils/logger";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const retryCount = useRef(0);
  // Track the pending retry timer and mount state so we can cancel in-flight
  // retries on unmount and avoid setting state on an unmounted component.
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const checkAuth = useCallback(async () => {
    try {
      const userData = await authService.getCurrentUser();
      if (!isMountedRef.current) return;
      setUser(userData);
      setLoading(false);
    } catch (error) {
      logger.warn("Auth check failed:", error);
      if (!isMountedRef.current) return;
      // If we failed, specifically in a dev/test environment where the server might be starting up,
      // we should retry a few times for the 'no-auth' check.
      if (retryCount.current < 5) {
        retryCount.current += 1;
        const delay = 1000 * retryCount.current;
        logger.debug(`Retrying auth check in ${delay}ms...`);
        retryTimeoutRef.current = setTimeout(checkAuth, delay);
      } else {
        localStorage.removeItem("auth_token");
        setLoading(false);
      }
    }
  }, []); // authService is a module-level singleton; no reactive deps needed

  useEffect(() => {
    isMountedRef.current = true;
    checkAuth();
    return () => {
      // Cancel any pending retry so we don't update state after unmount.
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [checkAuth]); // Include checkAuth per exhaustive-deps rule

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await authService.login(username, password);
      localStorage.setItem("auth_token", response.access_token);

      const userData = await authService.getCurrentUser();
      setUser(userData);
      return true;
    } catch (error) {
      logger.error("Login failed:", error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
