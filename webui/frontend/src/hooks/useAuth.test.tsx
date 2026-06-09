import React from "react";
import { renderHook, act, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { AuthProvider, useAuth } from "./useAuth";
import { authService } from "../services/authService";

// Mock the named export 'authService' object used by the hook
vi.mock("../services/authService", () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

const mockedAuthService = vi.mocked(authService);

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe("useAuth Hook", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
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
});
