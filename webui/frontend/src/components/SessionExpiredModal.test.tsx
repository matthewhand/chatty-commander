import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, test, vi, beforeEach } from "vitest";
import SessionExpiredModal from "./SessionExpiredModal";

// Mock useNavigate so we can assert the redirect target without a real router.
const navigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => navigate,
}));

// Mock useAuth so each test can drive the blocking state and observe the
// actions the modal invokes.
const confirmSessionExpiredSignIn = vi.fn();
const dismissSessionExpiredBlocking = vi.fn();
let blocking = true;
vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    sessionExpiredBlocking: blocking,
    confirmSessionExpiredSignIn,
    dismissSessionExpiredBlocking,
  }),
}));

describe("SessionExpiredModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    blocking = true;
  });

  test("renders nothing when not blocking", () => {
    blocking = false;
    const { container } = render(<SessionExpiredModal />);
    expect(container).toBeEmptyDOMElement();
    expect(
      screen.queryByTestId("session-expired-modal"),
    ).not.toBeInTheDocument();
  });

  test("shows the dialog with the unsaved-changes copy when blocking", () => {
    render(<SessionExpiredModal />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(
      screen.getByText(/Your unsaved changes are still here on this page/i),
    ).toBeInTheDocument();
  });

  test("'Sign in again' confirms the sign-out and navigates to /login", () => {
    render(<SessionExpiredModal />);
    fireEvent.click(screen.getByTestId("session-expired-signin"));
    expect(confirmSessionExpiredSignIn).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith("/login");
  });

  test("'Dismiss' hides the modal without signing out or navigating", () => {
    render(<SessionExpiredModal />);
    fireEvent.click(screen.getByTestId("session-expired-dismiss"));
    expect(dismissSessionExpiredBlocking).toHaveBeenCalledTimes(1);
    expect(confirmSessionExpiredSignIn).not.toHaveBeenCalled();
    expect(navigate).not.toHaveBeenCalled();
  });

  test("Escape does not dismiss the blocking modal", () => {
    render(<SessionExpiredModal />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(dismissSessionExpiredBlocking).not.toHaveBeenCalled();
    expect(confirmSessionExpiredSignIn).not.toHaveBeenCalled();
    // Still on screen.
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
