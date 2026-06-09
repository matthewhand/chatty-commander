import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import { ThemeProvider, useTheme } from "./ThemeProvider";

function ThemeProbe() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <button onClick={() => setTheme("light")}>set light</button>
    </div>
  );
}

function renderWithProviders(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ThemeProvider>{ui}</ThemeProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

describe("ThemeProvider", () => {
  test("loads the persisted theme from the backend config", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ui: { theme: "cupcake" } }),
    }) as any;

    renderWithProviders(<ThemeProbe />);

    await waitFor(() => {
      expect(screen.getByTestId("current-theme")).toHaveTextContent("cupcake");
    });
    expect(document.documentElement.getAttribute("data-theme")).toBe("cupcake");
    expect(global.fetch).toHaveBeenCalledWith("/api/v1/config");
  });

  test("falls back to the dark theme when the config endpoint is unreachable", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("offline")) as any;

    renderWithProviders(<ThemeProbe />);

    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
    await waitFor(() => {
      expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    });
  });

  test("setTheme updates the context and the document root attribute", async () => {
    // Config has no persisted theme -> keeps the default.
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    }) as any;

    renderWithProviders(<ThemeProbe />);

    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");

    fireEvent.click(screen.getByRole("button", { name: /set light/i }));

    expect(screen.getByTestId("current-theme")).toHaveTextContent("light");
    await waitFor(() => {
      expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    });
  });

  test("useTheme throws when used outside a ThemeProvider", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });
    expect(() => render(<ThemeProbe />)).toThrow(
      "useTheme must be used within a ThemeProvider",
    );
    consoleSpy.mockRestore();
  });
});
