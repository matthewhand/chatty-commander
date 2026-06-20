import React, { useState, useEffect, createContext, useContext, useRef, useCallback } from "react";
import {
  authService,
  subscribeSessionExpired,
  User,
} from "../services/authService";
import { hasUnsavedChanges } from "./useUnsavedChanges";
import { logger } from "../utils/logger";

/**
 * Window CustomEvent fired when the session expires mid-use. Lets any part of
 * the app (e.g. a toast surface mounted below the AuthProvider) react without
 * depending on React-context ordering. Detail carries the user-facing message.
 */
export const SESSION_EXPIRED_EVENT = "chatty:session-expired";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  /**
   * User-facing notice set when a previously-authenticated session is rejected
   * mid-session. Null when there is nothing to show. Consumers (e.g. the login
   * screen / a toast) can read this to explain the forced sign-out.
   */
  sessionExpiredNotice: string | null;
  /** Dismiss the {@link sessionExpiredNotice}. */
  clearSessionExpiredNotice: () => void;
  /**
   * True when the session has expired *while a form had unsaved changes* and we
   * have deliberately deferred clearing the user, so the page (and its
   * in-progress edits) stay mounted. A blocking modal is shown to the user
   * instead of an immediate redirect. False in the common case (no dirty forms),
   * where expiry behaves exactly as before — the user is cleared and
   * ProtectedRoute redirects to /login.
   */
  sessionExpiredBlocking: boolean;
  /**
   * True once the session has expired mid-use (with unsaved changes) and stays
   * true after the blocking modal is dismissed, until the user signs in again.
   * Unlike {@link sessionExpiredBlocking}, this does NOT get cleared on dismiss,
   * so the app can honestly show a persistent "session expired" banner instead
   * of pretending the page is still logged in. Cleared only by a successful
   * login or by confirming the sign-out.
   */
  sessionExpired: boolean;
  /**
   * Commit the deferred sign-out: clear the in-memory user so ProtectedRoute
   * redirects to /login. Called from the blocking modal's "Sign in again"
   * action once the user has had a chance to copy/save their edits.
   */
  confirmSessionExpiredSignIn: () => void;
  /**
   * Hide the blocking modal without signing out, keeping the user on the page in
   * the expired state so they can copy/save-attempt their edits. The modal
   * re-shows on the next 401.
   */
  dismissSessionExpiredBlocking: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState<
    string | null
  >(null);
  // True when we've deferred the forced sign-out because a form had unsaved
  // edits; drives the blocking SessionExpiredModal instead of an immediate
  // redirect.
  const [sessionExpiredBlocking, setSessionExpiredBlocking] = useState(false);
  // Persistent expired latch: stays true after the blocking modal is dismissed
  // so a non-blocking "session expired" banner can remain until the user signs
  // in again. Distinct from sessionExpiredBlocking, which only gates the modal.
  const [sessionExpired, setSessionExpired] = useState(false);
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

  // Centralised session-expiry handling. The token has already been cleared by
  // authService.notifySessionExpired(); here we surface a notice and broadcast a
  // window event so any toast surface mounted elsewhere in the tree can react.
  //
  // The branch: if NO form has unsaved edits (the common case), behave exactly
  // as before — drop the in-memory user so ProtectedRoute redirects to /login.
  // If a dirty form IS mounted, do NOT clear the user yet: keep the page (and
  // its unsaved edits) on screen and raise a blocking modal instead, so the
  // user can copy/save before signing in again.
  useEffect(() => {
    const unsubscribe = subscribeSessionExpired((message) => {
      if (!isMountedRef.current) return;
      setSessionExpiredNotice(message);
      if (hasUnsavedChanges()) {
        // Defer the sign-out; the modal drives confirmSessionExpiredSignIn().
        // Latch the persistent expired flag too so that, if the modal is later
        // dismissed, a non-blocking banner remains until the user signs in.
        setSessionExpiredBlocking(true);
        setSessionExpired(true);
      } else {
        setUser(null);
        setLoading(false);
      }
      try {
        window.dispatchEvent(
          new CustomEvent(SESSION_EXPIRED_EVENT, { detail: { message } }),
        );
      } catch {
        /* environments without CustomEvent (non-browser) — notice still set */
      }
    });
    return unsubscribe;
  }, []);

  // Cross-tab auth sync. `storage` events fire in *other* tabs when this or
  // another tab mutates localStorage, so when one tab logs out/expires (token
  // removed) or logs in (token set) the rest follow suit instead of drifting
  // out of sync. SSR-safe: guarded on `window` existing.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onStorage = (event: StorageEvent) => {
      // Only react to our own token key (null key => storage.clear()).
      if (event.key !== null && event.key !== "auth_token") return;
      if (!isMountedRef.current) return;
      if (event.newValue) {
        // A token appeared in another tab (login elsewhere) — pick up the
        // session here by re-running the normal auth check.
        retryCount.current = 0;
        checkAuth();
      } else {
        // Token removed elsewhere (logout/expiry) — reflect unauthenticated.
        setUser(null);
        setLoading(false);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [checkAuth]);

  const clearSessionExpiredNotice = useCallback(() => {
    setSessionExpiredNotice(null);
  }, []);

  // Commit the deferred sign-out: now that the user has had a chance to copy
  // their edits, drop the in-memory user so ProtectedRoute redirects to /login.
  const confirmSessionExpiredSignIn = useCallback(() => {
    setSessionExpiredBlocking(false);
    // Committing the sign-out resolves the expired state — the user is heading
    // to /login, so the persistent banner no longer applies.
    setSessionExpired(false);
    setUser(null);
    setLoading(false);
  }, []);

  // Hide the blocking modal but keep the user on the page in the expired state.
  // We deliberately leave the user non-null so the route stays mounted; the
  // modal re-shows on the next 401 (the expiry latch re-arms only on a fresh
  // successful auth).
  const dismissSessionExpiredBlocking = useCallback(() => {
    setSessionExpiredBlocking(false);
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await authService.login(username, password);
      localStorage.setItem("auth_token", response.access_token);

      const userData = await authService.getCurrentUser();
      setUser(userData);
      // A successful sign-in supersedes any stale expiry notice / blocking modal
      // and clears the persistent expired banner.
      setSessionExpiredNotice(null);
      setSessionExpiredBlocking(false);
      setSessionExpired(false);
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
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
        sessionExpiredNotice,
        clearSessionExpiredNotice,
        sessionExpiredBlocking,
        sessionExpired,
        confirmSessionExpiredSignIn,
        dismissSessionExpiredBlocking,
      }}
    >
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
