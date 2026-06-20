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

// Mirror the live AVAILABLE_THEMES from ThemeProvider so we can assert the
// switcher renders human-readable labels for every real theme.
const REAL_THEMES = [
  "light",
  "dark",
  "corporate",
  "business",
  "emerald",
  "nord",
];

vi.mock("./ThemeProvider", () => ({
  useTheme: () => ({
    theme: "dark",
    setTheme: vi.fn(),
    availableThemes: REAL_THEMES,
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
  test("sticky desktop header hosts the breadcrumb but no page-title heading", () => {
    renderAt("/commands/authoring");

    // The persistent app bar is a sticky <header> in the scroll area.
    const headers = screen.getAllByRole("banner");
    const stickyHeader = headers.find((h) =>
      h.className.includes("sticky"),
    );
    expect(stickyHeader).toBeDefined();
    const header = stickyHeader as HTMLElement;
    expect(header.className).toContain("top-0");

    // Breadcrumb is hosted in the header (deep route => parent crumb present).
    expect(within(header).getByText("Commands")).toBeInTheDocument();

    // Regression: the header must NOT render its own page-title heading, which
    // previously duplicated each page's hero title.
    expect(
      within(header).queryByRole("heading"),
    ).not.toBeInTheDocument();
  });

  test("does not render a duplicate page-title heading from the layout", () => {
    // The page body MainLayout renders ("page body") contains no heading; any
    // heading would be a layout-injected duplicate of a page's own title.
    renderAt("/commands/authoring");
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });

  test("theme switcher renders human-readable labels for the real themes", () => {
    renderAt("/dashboard");

    const select = screen.getByRole("combobox", { name: "Select theme" });
    const options = within(select).getAllByRole("option");
    const labels = options.map((o) => o.textContent);

    expect(labels).toEqual([
      "Light",
      "Dark",
      "Corporate",
      "Business",
      "Emerald",
      "Nord",
    ]);

    // None of the option labels should be a raw lowercase token.
    for (const label of labels) {
      expect(label).not.toMatch(/^[a-z]/);
    }
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
