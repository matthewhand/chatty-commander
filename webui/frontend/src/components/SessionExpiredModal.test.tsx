import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, test, vi, beforeEach } from "vitest";
import SessionExpiredModal from "./SessionExpiredModal";

// Mock useNavigate so we can assert the redirect target without a real router.
const navigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => navigate,
}));

// Mock useAuth so each test can drive the blocking/expired state and observe
// the actions the modal invokes.
const confirmSessionExpiredSignIn = vi.fn();
const dismissSessionExpiredBlocking = vi.fn();
let blocking = true;
let expired = true;
vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    sessionExpiredBlocking: blocking,
    sessionExpired: expired,
    confirmSessionExpiredSignIn,
    dismissSessionExpiredBlocking,
  }),
}));

describe("SessionExpiredModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    blocking = true;
    expired = true;
    document.body.style.overflow = "";
  });

  test("renders nothing when not blocking and not expired", () => {
    blocking = false;
    expired = false;
    const { container } = render(<SessionExpiredModal />);
    expect(container).toBeEmptyDOMElement();
    expect(
      screen.queryByTestId("session-expired-modal"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("session-expired-banner"),
    ).not.toBeInTheDocument();
  });

  test("shows the dialog with the honest saving-disabled copy when blocking", () => {
    render(<SessionExpiredModal />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(
      screen.getByText(/Saving is disabled until you sign in again/i),
    ).toBeInTheDocument();
    // Banner is not shown while the blocking modal is up.
    expect(
      screen.queryByTestId("session-expired-banner"),
    ).not.toBeInTheDocument();
  });

  test("relabels the dismiss action to 'Keep page open'", () => {
    render(<SessionExpiredModal />);
    const dismiss = screen.getByTestId("session-expired-dismiss");
    expect(dismiss).toHaveTextContent(/Keep page open/i);
  });

  test("'Sign in again' confirms the sign-out and navigates to /login", () => {
    render(<SessionExpiredModal />);
    fireEvent.click(screen.getByTestId("session-expired-signin"));
    expect(confirmSessionExpiredSignIn).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith("/login");
  });

  test("'Keep page open' hides the modal without signing out or navigating", () => {
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

  test("locks body scroll while blocking and restores it on unmount", () => {
    const { unmount } = render(<SessionExpiredModal />);
    expect(document.body.style.overflow).toBe("hidden");
    unmount();
    expect(document.body.style.overflow).toBe("");
  });

  test("after dismiss, the persistent banner is shown and the modal is gone", () => {
    // Dismissed state: blocking lifted but the session is still expired.
    blocking = false;
    expired = true;
    render(<SessionExpiredModal />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const banner = screen.getByTestId("session-expired-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/Session expired/i);
    // Banner does not lock body scroll (non-blocking).
    expect(document.body.style.overflow).toBe("");
  });

  test("the banner 'Sign in' button confirms the sign-out and navigates", () => {
    blocking = false;
    expired = true;
    render(<SessionExpiredModal />);

    fireEvent.click(screen.getByTestId("session-expired-banner-signin"));
    expect(confirmSessionExpiredSignIn).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith("/login");
  });
});
