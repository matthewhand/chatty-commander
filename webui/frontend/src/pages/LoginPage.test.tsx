/* eslint-disable testing-library/no-node-access */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import LoginPage from "./LoginPage";
import { useAuth } from "../hooks/useAuth";
import { authService } from "../services/authService";

// The page drives the real auth flow through useAuth; mock the hook so we can
// control success/failure, and the service so we can set the failure kind.
vi.mock("../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../services/authService", () => ({
  authService: { lastLoginErrorKind: null },
}));

const mockedUseAuth = vi.mocked(useAuth);

const clearSessionExpiredNotice = vi.fn();

const setLogin = (
  login: (u: string, p: string) => Promise<boolean>,
  sessionExpiredNotice: string | null = null,
) => {
  mockedUseAuth.mockReturnValue({
    user: null,
    isAuthenticated: false,
    login,
    logout: vi.fn(),
    loading: false,
    sessionExpiredNotice,
    clearSessionExpiredNotice,
  });
};

const fillAndSubmit = () => {
  fireEvent.change(screen.getByLabelText("Username"), {
    target: { value: "alice" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "secret" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Login" }));
};

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authService.lastLoginErrorKind = null;
  });

  test("renders the unified ChattyCommander logo/wordmark", () => {
    setLogin(vi.fn());
    render(<LoginPage />);
    // The two-column layout renders the brand lockup in the desktop hero panel
    // AND (for small screens) in the form card; both live in the DOM since the
    // show/hide is CSS-only. Assert the brand is present (at least once).
    expect(
      screen.getAllByRole("img", { name: "ChattyCommander" }).length,
    ).toBeGreaterThanOrEqual(1);
    // Wordmark renders the unified name, not the old "Chatty Commander" split.
    expect(screen.getAllByText("Chatty").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Commander").length).toBeGreaterThanOrEqual(1);
  });

  test("login background uses an intentional treatment, not the dead pattern class", () => {
    setLogin(vi.fn());
    const { container } = render(<LoginPage />);
    const wrapper = container.firstElementChild as HTMLElement;
    // The undefined `pattern-isometric` utility was a no-op; it must be gone.
    expect(wrapper.className).not.toContain("pattern-isometric");
    // Background is now a deliberate gradient built from existing utilities.
    expect(wrapper.className).toContain("bg-gradient-to-br");
  });

  test("does not leak internal CLI flags in helper copy", () => {
    setLogin(vi.fn());
    const { container } = render(<LoginPage />);
    expect(container.textContent).not.toMatch(/--no-auth/);
    expect(container.textContent).not.toMatch(/CLI/);
    expect(
      screen.getByText(/managed by your administrator/i),
    ).toBeInTheDocument();
  });

  test("failed login announces the error and clears the password", async () => {
    authService.lastLoginErrorKind = "credentials";
    setLogin(vi.fn().mockResolvedValue(false));
    render(<LoginPage />);

    const password = screen.getByLabelText("Password") as HTMLInputElement;
    fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/invalid username or password/i);
    expect(alert).toHaveAttribute("aria-live", "assertive");

    // Password is cleared and refocused so the user can immediately retry.
    await waitFor(() => expect(password.value).toBe(""));
    expect(password).toHaveFocus();

    // Inputs are linked to the error for assistive tech.
    expect(password).toHaveAttribute("aria-invalid", "true");
    expect(password).toHaveAttribute("aria-describedby", "login-error");
  });

  test("network failure shows a reachability message, not bad credentials", async () => {
    authService.lastLoginErrorKind = "network";
    setLogin(vi.fn().mockResolvedValue(false));
    render(<LoginPage />);

    fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/can't reach the server/i);
  });

  test("shows the session-expired notice when the hook provides one", () => {
    setLogin(vi.fn(), "Your session expired — please sign in again");
    render(<LoginPage />);

    const notice = screen.getByRole("status");
    expect(notice).toHaveTextContent(/session expired/i);
  });

  test("no session-expired notice is rendered when the hook has none", () => {
    setLogin(vi.fn(), null);
    render(<LoginPage />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  test("starting a new login clears the session-expired notice", async () => {
    setLogin(
      vi.fn().mockResolvedValue(true),
      "Your session expired — please sign in again",
    );
    render(<LoginPage />);

    fillAndSubmit();

    await waitFor(() =>
      expect(clearSessionExpiredNotice).toHaveBeenCalled(),
    );
  });

  test("password visibility toggle flips the input type", () => {
    setLogin(vi.fn());
    render(<LoginPage />);

    const password = screen.getByLabelText("Password") as HTMLInputElement;
    expect(password.type).toBe("password");

    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(toggle);
    expect(password.type).toBe("text");
    expect(
      screen.getByRole("button", { name: "Hide password" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
