import React from "react";
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import MainLayout from "./MainLayout";

// MainLayout pulls logout from useAuth and the theme select from ThemeProvider;
// mock both so the layout renders without an AuthProvider/QueryClient.
vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false,
  }),
}));

vi.mock("./ThemeProvider", () => ({
  useTheme: () => ({
    theme: "dark",
    setTheme: vi.fn(),
    availableThemes: ["light", "dark"],
  }),
}));

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <MainLayout>
        <div>page body</div>
      </MainLayout>
    </MemoryRouter>,
  );
}

describe("MainLayout", () => {
  test("sticky desktop header shows the page title and breadcrumb", () => {
    renderAt("/commands/authoring");

    // The persistent app bar is a sticky <header> in the scroll area.
    const headers = screen.getAllByRole("banner");
    const stickyHeader = headers.find((h) =>
      h.className.includes("sticky"),
    );
    expect(stickyHeader).toBeDefined();
    const header = stickyHeader as HTMLElement;
    expect(header.className).toContain("top-0");

    // Page title derived from the route.
    expect(
      within(header).getByRole("heading", { name: "Command Authoring" }),
    ).toBeInTheDocument();

    // Breadcrumb is hosted in the header (deep route => parent crumb present).
    expect(within(header).getByText("Commands")).toBeInTheDocument();
  });

  test("renders the ChattyCommander logo in the sidebar", () => {
    renderAt("/dashboard");
    const logos = screen.getAllByRole("img", { name: "ChattyCommander" });
    // At least the sidebar lockup is present.
    expect(logos.length).toBeGreaterThanOrEqual(1);
  });

  test("does not regress nav active-state (aria-current on the active link)", () => {
    renderAt("/commands");
    // Exact name avoids matching the "Command Authoring" nav link.
    const activeLink = screen.getByRole("link", { name: "Commands" });
    expect(activeLink).toHaveAttribute("aria-current", "page");
  });
});
