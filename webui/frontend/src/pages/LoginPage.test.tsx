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

const setLogin = (login: (u: string, p: string) => Promise<boolean>) => {
  mockedUseAuth.mockReturnValue({
    user: null,
    isAuthenticated: false,
    login,
    logout: vi.fn(),
    loading: false,
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
