import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, vi } from "vitest";
// framer-motion caches the reduced-motion preference in this module-level
// singleton (read once on first useReducedMotion() call). We reset it per-test
// so a freshly-mocked matchMedia is re-read instead of a stale cached value.
import { hasReducedMotionListener, prefersReducedMotion } from "motion-dom";
import CommandsPage from "./CommandsPage";
import { apiService } from "../services/apiService";

// Force `prefers-reduced-motion: reduce` to report as active so framer-motion's
// useReducedMotion() hook returns true. Other media queries keep the default
// (matches: false) behaviour from setupTests.ts.
function mockReducedMotion(prefersReduced: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: prefersReduced && query.includes("prefers-reduced-motion"),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia;
  // Invalidate framer-motion's cache so the new matchMedia value is picked up.
  hasReducedMotionListener.current = false;
  prefersReducedMotion.current = null;
}

vi.mock("../services/apiService", () => ({
  apiService: { getCommands: vi.fn() },
}));

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CommandsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    take_screenshot: { action: "keypress", keys: "alt+print_screen" },
    open_docs: { action: "url", url: "https://example.com/docs" },
  });
});

afterEach(() => {
  // Restore the default matchMedia stub so other tests are unaffected.
  mockReducedMotion(false);
});

test("each command card shows its name", async () => {
  renderPage();
  // The command name is the card title (previously the card was anonymous).
  expect(await screen.findByText("take_screenshot")).toBeInTheDocument();
  expect(await screen.findByText("open_docs")).toBeInTheDocument();
});

test("each card describes the command's actual action", async () => {
  renderPage();
  // keypress command shows the keys it presses
  expect(await screen.findByText("Presses keys")).toBeInTheDocument();
  expect(await screen.findByText("alt+print_screen")).toBeInTheDocument();
  // url command shows the URL it opens
  expect(await screen.findByText("Opens URL")).toBeInTheDocument();
  expect(
    await screen.findByText("https://example.com/docs")
  ).toBeInTheDocument();
});

test("respects prefers-reduced-motion: reduce on the card cascade", async () => {
  mockReducedMotion(true);
  renderPage();

  // Wait for cards to render.
  await screen.findByText("take_screenshot");

  const cards = screen.getAllByTestId('command-card-motion');
  expect(cards.length).toBeGreaterThan(0);

  cards.forEach((card) => {
    // The reduced-motion branch must be taken for every cascade card...
    expect(card.getAttribute("data-reduced-motion")).toBe("true");
    // ...and no entrance transform/opacity should be applied inline, so the
    // final rendered state is shown immediately with no staggered delay.
    const style = card.style;
    expect(style.transform === "" || style.transform === "none").toBe(true);
    expect(style.opacity === "" || style.opacity === "1").toBe(true);
    expect(style.transitionDelay).toBe("");
  });
});

test("applies the staggered cascade when motion is allowed", async () => {
  mockReducedMotion(false);
  renderPage();

  await screen.findByText("take_screenshot");

  const cards = screen.getAllByTestId('command-card-motion');
  expect(cards.length).toBeGreaterThan(0);
  cards.forEach((card) => {
    expect(card.getAttribute("data-reduced-motion")).toBe("false");
  });
});
