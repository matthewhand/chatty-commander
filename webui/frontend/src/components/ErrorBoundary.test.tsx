import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import ErrorBoundary from "./ErrorBoundary";

function Boom(): React.ReactElement {
  throw new Error("kaboom");
}

describe("ErrorBoundary", () => {
  test("renders children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div>safe content</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("safe content")).toBeInTheDocument();
  });

  test("renders a branded fallback with a reload action when a child throws", () => {
    // Suppress React's expected error logging for this render.
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reload page/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/kaboom/)).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test("uses a custom fallback when provided", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary fallback={(err) => <div>custom: {err.message}</div>}>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByText("custom: kaboom")).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  test("the reload button calls window.location.reload", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const reloadSpy = vi.fn();
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...window.location, reload: reloadSpy },
    });

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole("button", { name: /reload page/i }));
    expect(reloadSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
