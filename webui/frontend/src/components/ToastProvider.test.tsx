import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ToastProvider, useToast } from "./ToastProvider";

function Trigger({
  message,
  type,
}: {
  message: string;
  type: "success" | "error" | "info" | "warning";
}) {
  const { addToast } = useToast();
  return <button onClick={() => addToast(message, type)}>add</button>;
}

function renderWithToast(
  message: string,
  type: "success" | "error" | "info" | "warning" = "success",
) {
  return render(
    <ToastProvider>
      <Trigger message={message} type={type} />
    </ToastProvider>,
  );
}

describe("ToastProvider", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders toasts inside an aria-live region", () => {
    renderWithToast("Saved!");
    const region = screen.getByRole("region", { name: /notifications/i });
    expect(region).toHaveAttribute("aria-live", "polite");

    fireEvent.click(screen.getByText("add"));

    // Success toasts announce politely via role="status".
    const toast = screen.getByRole("status");
    expect(toast).toHaveTextContent("Saved!");
    expect(region).toContainElement(toast);
  });

  it("uses an assertive alert for error toasts", () => {
    renderWithToast("Boom", "error");
    fireEvent.click(screen.getByText("add"));
    const toast = screen.getByRole("alert");
    expect(toast).toHaveTextContent("Boom");
    expect(toast).toHaveAttribute("aria-live", "assertive");
  });

  it("can be dismissed via the close button", async () => {
    renderWithToast("Dismiss me");
    fireEvent.click(screen.getByText("add"));
    expect(screen.getByText("Dismiss me")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /dismiss notification/i }),
    );

    await waitFor(() =>
      expect(screen.queryByText("Dismiss me")).not.toBeInTheDocument(),
    );
  });

  it("auto-dismisses after the timeout", async () => {
    render(
      <ToastProvider>
        <Trigger message="Auto" type="info" />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText("add"));
    expect(screen.getByText("Auto")).toBeInTheDocument();

    // Real timers: the toast is removed from state after ~3s, then the
    // framer-motion exit animation unmounts it. Allow ample time.
    await waitFor(
      () => expect(screen.queryByText("Auto")).not.toBeInTheDocument(),
      { timeout: 6000 },
    );
  }, 8000);

  it("pauses auto-dismiss on hover and resumes on leave", async () => {
    render(
      <ToastProvider>
        <Trigger message="Hovered" type="info" />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText("add"));
    const toast = screen.getByRole("status");

    // Hover clears the auto-dismiss timer; it should still be present after
    // longer than the normal lifetime.
    fireEvent.mouseEnter(toast);
    await new Promise((resolve) => setTimeout(resolve, 3500));
    expect(screen.getByText("Hovered")).toBeInTheDocument();

    // Leaving restarts the timer, after which it dismisses.
    fireEvent.mouseLeave(toast);
    await waitFor(
      () => expect(screen.queryByText("Hovered")).not.toBeInTheDocument(),
      { timeout: 6000 },
    );
  }, 12000);
});
