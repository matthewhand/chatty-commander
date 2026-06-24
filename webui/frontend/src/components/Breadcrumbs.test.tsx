import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Breadcrumbs from "./Breadcrumbs";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Breadcrumbs />
    </MemoryRouter>,
  );
}

describe("Breadcrumbs", () => {
  test("renders nothing at the dashboard/home level (no duplicate Home)", () => {
    renderAt("/dashboard");
    expect(screen.queryByRole("navigation")).toBeNull();
  });

  test("does not duplicate Home when the first segment resolves to Home", () => {
    // /commands -> Home / Commands (Home is synthetic, /commands is real).
    renderAt("/commands");
    const links = screen.getAllByRole("link").map((a) => a.textContent);
    // Exactly one "Home" crumb.
    expect(links.filter((t) => t === "Home")).toHaveLength(1);
    expect(screen.getByText("Commands")).toBeInTheDocument();
  });

  test("maps deep routes via pathNameMap (commands/authoring)", () => {
    renderAt("/commands/authoring");
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Commands")).toBeInTheDocument();
    // Deep route label is human-readable, not the raw "authoring" segment.
    expect(screen.getByText("Command Authoring")).toBeInTheDocument();
  });

  test("marks the final crumb with aria-current=page", () => {
    renderAt("/configuration");
    const current = screen.getByText("Configuration");
    expect(current).toHaveAttribute("aria-current", "page");
    expect(current.tagName.toLowerCase()).toBe("span");
  });
});
