import React from "react";
import { renderHook, act, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { AuthProvider, useAuth } from "./useAuth";
import { authService } from "../services/authService";
import {
  __resetUnsavedChanges,
  useUnsavedChanges,
} from "./useUnsavedChanges";

// Captures the session-expiry listener the hook registers, so tests can drive
// the expiry path directly. The mock's subscribe stores the latest listener and
// returns an unsubscribe.
let sessionExpiredListener: ((message: string) => void) | null = null;

// Mock the named export 'authService' object used by the hook, plus the
// module-level session-expiry pub/sub helpers it subscribes to.
vi.mock("../services/authService", () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
  subscribeSessionExpired: (listener: (message: string) => void) => {
    sessionExpiredListener = listener;
    return () => {
      if (sessionExpiredListener === listener) sessionExpiredListener = null;
    };
  },
  SESSION_EXPIRED_MESSAGE: "Your session expired — please sign in again",
}));

const mockedAuthService = vi.mocked(authService);

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe("useAuth Hook", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    __resetUnsavedChanges();
  });

  test("throws when used outside an AuthProvider", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });
    expect(() => renderHook(() => useAuth())).toThrow(
      "useAuth must be used within an AuthProvider",
    );
    consoleSpy.mockRestore();
  });

  test("initializes with no user when auth check fails", async () => {
    mockedAuthService.getCurrentUser.mockRejectedValue(
      new Error("Authentication required"),
    );

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);

    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.user).toBeNull();

    // Unmount cancels the pending auth-check retry timer.
    unmount();
  });

  test("restores an existing session on mount", async () => {
    const mockUser = {
      username: "existing-user",
      is_active: true,
      roles: ["user"],
    };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.loading).toBe(false);
    expect(mockedAuthService.getCurrentUser).toHaveBeenCalled();
  });

  test("handles login successfully and stores the token", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    // Mount-time check fails (not logged in yet)...
    mockedAuthService.getCurrentUser
      .mockRejectedValueOnce(new Error("Authentication required"))
      // ...then succeeds after login stores the token.
      .mockResolvedValueOnce(mockUser);
    mockedAuthService.login.mockResolvedValueOnce({
      access_token: "test-token",
      token_type: "bearer",
      expires_in: 3600,
    });

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });

    let ok = false;
    await act(async () => {
      ok = await result.current.login("testuser", "password");
    });

    expect(ok).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(localStorage.getItem("auth_token")).toBe("test-token");

    unmount();
  });

  test("login returns false on failure", async () => {
    mockedAuthService.getCurrentUser.mockRejectedValue(
      new Error("Authentication required"),
    );
    mockedAuthService.login.mockRejectedValueOnce(new Error("Login failed"));
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });

    let ok = true;
    await act(async () => {
      ok = await result.current.login("wrong", "credentials");
    });

    expect(ok).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);

    consoleSpy.mockRestore();
    unmount();
  });

  test("session expiry clears the user and surfaces a notice", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Become authenticated first.
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
    expect(result.current.sessionExpiredNotice).toBeNull();

    // Fire the session-expiry event the hook subscribed to (as authService
    // would after a mid-session 401).
    act(() => {
      sessionExpiredListener?.("Your session expired — please sign in again");
    });

    // User cleared => ProtectedRoute will redirect to /login; notice is shown.
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.sessionExpiredNotice).toBe(
      "Your session expired — please sign in again",
    );
  });

  test("session expiry dispatches a window event consumers can observe", async () => {
    mockedAuthService.getCurrentUser.mockResolvedValue({
      username: "testuser",
      is_active: true,
      roles: ["user"],
    });

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    const handler = vi.fn();
    window.addEventListener("chatty:session-expired", handler);

    act(() => {
      sessionExpiredListener?.("expired");
    });

    expect(handler).toHaveBeenCalledTimes(1);
    window.removeEventListener("chatty:session-expired", handler);
    unmount();
  });

  test("clearSessionExpiredNotice dismisses the notice", async () => {
    mockedAuthService.getCurrentUser.mockResolvedValue({
      username: "testuser",
      is_active: true,
      roles: ["user"],
    });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    expect(result.current.sessionExpiredNotice).toBe("expired");

    act(() => result.current.clearSessionExpiredNotice());
    expect(result.current.sessionExpiredNotice).toBeNull();
  });

  test("a storage event removing the token logs the tab out (cross-tab sync)", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    // Another tab logged out: the token is removed and a storage event fires.
    act(() => {
      localStorage.removeItem("auth_token");
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "auth_token",
          oldValue: "test-token",
          newValue: null,
        }),
      );
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);

    unmount();
  });

  test("a storage event adding a token re-checks auth (cross-tab login)", async () => {
    // Start unauthenticated: mount-time check rejects.
    mockedAuthService.getCurrentUser.mockRejectedValue(
      new Error("Authentication required"),
    );

    const { result, unmount } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() =>
      expect(mockedAuthService.getCurrentUser).toHaveBeenCalled(),
    );
    expect(result.current.isAuthenticated).toBe(false);
    const callsBefore = mockedAuthService.getCurrentUser.mock.calls.length;

    // Another tab logs in: a token appears and a storage event fires, so this
    // tab re-runs the auth check and adopts the now-valid session.
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);

    act(() => {
      localStorage.setItem("auth_token", "fresh-token");
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "auth_token",
          oldValue: null,
          newValue: "fresh-token",
        }),
      );
    });

    // The storage handler re-invoked the auth check...
    expect(mockedAuthService.getCurrentUser.mock.calls.length).toBeGreaterThan(
      callsBefore,
    );
    // ...and the session is adopted.
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
    expect(result.current.user).toEqual(mockUser);

    unmount();
  });

  test("logout clears the user and token", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem("auth_token")).toBeNull();
  });

  test("expiry with NO unsaved changes redirects immediately (user cleared, not blocking)", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));

    // Unchanged behaviour: user cleared so ProtectedRoute redirects; no modal.
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.sessionExpiredBlocking).toBe(false);
  });

  test("expiry WITH unsaved changes shows blocking modal without clearing the user", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    // Render the auth hook alongside a registered "dirty form".
    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));

    // Deferred: the user (and their page/edits) stay mounted; modal blocks.
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.sessionExpiredBlocking).toBe(true);
    expect(result.current.sessionExpiredNotice).toBe("expired");
  });

  test("confirmSessionExpiredSignIn clears the user and lifts the block", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    expect(result.current.sessionExpiredBlocking).toBe(true);

    act(() => result.current.confirmSessionExpiredSignIn());

    expect(result.current.sessionExpiredBlocking).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test("dismissSessionExpiredBlocking hides the modal but keeps the user signed in", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    expect(result.current.sessionExpiredBlocking).toBe(true);

    act(() => result.current.dismissSessionExpiredBlocking());

    // Modal hidden, but the user stays on the page (still "authenticated" in
    // memory) so they can copy/save their edits.
    expect(result.current.sessionExpiredBlocking).toBe(false);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  test("dismiss leaves a persistent sessionExpired flag (drives the banner)", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    // Both the blocking gate and the persistent latch are set on expiry.
    expect(result.current.sessionExpiredBlocking).toBe(true);
    expect(result.current.sessionExpired).toBe(true);

    act(() => result.current.dismissSessionExpiredBlocking());

    // Modal gone, but the persistent expired latch remains so the app can show
    // the non-blocking banner until the user signs in.
    expect(result.current.sessionExpiredBlocking).toBe(false);
    expect(result.current.sessionExpired).toBe(true);
  });

  test("confirmSessionExpiredSignIn clears the persistent sessionExpired flag", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    act(() => result.current.dismissSessionExpiredBlocking());
    expect(result.current.sessionExpired).toBe(true);

    act(() => result.current.confirmSessionExpiredSignIn());
    expect(result.current.sessionExpired).toBe(false);
  });

  test("a successful login clears the persistent sessionExpired flag", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(
      () => {
        useUnsavedChanges(true);
        return useAuth();
      },
      { wrapper },
    );
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));
    act(() => result.current.dismissSessionExpiredBlocking());
    expect(result.current.sessionExpired).toBe(true);

    mockedAuthService.login.mockResolvedValueOnce({
      access_token: "fresh-token",
      token_type: "bearer",
      expires_in: 3600,
    });

    await act(async () => {
      await result.current.login("testuser", "password");
    });

    expect(result.current.sessionExpired).toBe(false);
    expect(result.current.sessionExpiredBlocking).toBe(false);
  });

  test("the no-unsaved-changes path does not set the persistent sessionExpired flag", async () => {
    const mockUser = { username: "testuser", is_active: true, roles: ["user"] };
    mockedAuthService.getCurrentUser.mockResolvedValue(mockUser);
    localStorage.setItem("auth_token", "test-token");

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => sessionExpiredListener?.("expired"));

    // Immediate-redirect path: user cleared, and neither expired flag is set.
    expect(result.current.user).toBeNull();
    expect(result.current.sessionExpiredBlocking).toBe(false);
    expect(result.current.sessionExpired).toBe(false);
  });
});
