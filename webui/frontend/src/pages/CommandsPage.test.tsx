import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
// framer-motion caches the reduced-motion preference in this module-level
// singleton (read once on first useReducedMotion() call). We reset it per-test
// so a freshly-mocked matchMedia is re-read instead of a stale cached value.
import { hasReducedMotionListener, prefersReducedMotion } from "motion-dom";
import CommandsPage from "./CommandsPage";
import { ToastProvider } from "../components/ToastProvider";
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
  apiService: {
    getCommands: vi.fn(),
    deleteCommand: vi.fn(),
    updateConfig: vi.fn(),
  },
}));

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter>
          <CommandsPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  // jsdom does not implement HTMLDialogElement.showModal/close; stub them so the
  // delete/import confirmation dialogs can be exercised.
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal() {
      this.open = true;
    };
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function close() {
      this.open = false;
    };
  }
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    take_screenshot: { action: "keypress", keys: "alt+print_screen" },
    open_docs: { action: "url", url: "https://example.com/docs" },
  });
  (apiService.deleteCommand as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
  (apiService.updateConfig as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
});

afterEach(() => {
  vi.clearAllMocks();
  // Restore the default matchMedia stub so other tests are unaffected.
  mockReducedMotion(false);
});

test("each command row shows its name", async () => {
  renderPage();
  expect(await screen.findByText("take_screenshot")).toBeInTheDocument();
  expect(await screen.findByText("open_docs")).toBeInTheDocument();
});

test("each row describes the command's actual action", async () => {
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

test("renders a distinct type badge per command type", async () => {
  renderPage();
  // keypress -> "Keypress" badge, url -> "URL" badge (not the same label).
  expect(await screen.findByText("Keypress")).toBeInTheDocument();
  expect(await screen.findByText("URL")).toBeInTheDocument();
});

test("infers the type from the payload when action is missing", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    run_thing: { cmd: "echo hi" },
    say_hi: { message: "hello there" },
  });
  renderPage();
  expect(await screen.findByText("Shell")).toBeInTheDocument();
  expect(await screen.findByText("Message")).toBeInTheDocument();
});

test("default sort is alphabetical by name", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    zeta: { action: "url", url: "https://z.example" },
    alpha: { action: "url", url: "https://a.example" },
  });
  renderPage();
  await screen.findByText("alpha");
  const rows = document.querySelectorAll("tbody tr");
  const names = Array.from(rows).map(
    (r) => r.querySelector("td")?.textContent?.trim()
  );
  expect(names).toEqual(["alpha", "zeta"]);
});

test("sorting by type groups commands by their type", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    aaa_url: { action: "url", url: "https://a.example" },
    bbb_key: { action: "keypress", keys: "ctrl+a" },
  });
  renderPage();
  await screen.findByText("aaa_url");
  // Switch sort to "type". Keypress < URL alphabetically, so bbb_key comes first.
  fireEvent.change(screen.getByLabelText("Sort commands"), {
    target: { value: "type" },
  });
  await waitFor(() => {
    const rows = document.querySelectorAll("tbody tr");
    const names = Array.from(rows).map(
      (r) => r.querySelector("td")?.textContent?.trim()
    );
    expect(names).toEqual(["bbb_key", "aaa_url"]);
  });
});

test("search matches the visible detail, not just the name", async () => {
  renderPage();
  await screen.findByText("take_screenshot");
  fireEvent.change(screen.getByLabelText("Search commands"), {
    target: { value: "print_screen" },
  });
  // Only the keypress command (whose detail contains print_screen) should remain.
  await waitFor(() => {
    expect(screen.getByText("take_screenshot")).toBeInTheDocument();
    expect(screen.queryByText("open_docs")).not.toBeInTheDocument();
  });
});

test("delete failure surfaces a toast instead of window.alert", async () => {
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
  (apiService.deleteCommand as ReturnType<typeof vi.fn>).mockRejectedValue(
    new Error("boom")
  );
  renderPage();
  await screen.findByText("take_screenshot");

  fireEvent.click(screen.getByLabelText("Delete take_screenshot"));
  fireEvent.click(screen.getByRole("button", { name: "Delete" }));

  const toast = await screen.findByText(/Failed to delete command: boom/);
  expect(toast).toBeInTheDocument();
  expect(alertSpy).not.toHaveBeenCalled();
  alertSpy.mockRestore();
});

test("each row exposes direct Edit and Delete controls", async () => {
  renderPage();
  await screen.findByText("take_screenshot");
  expect(
    screen.getByLabelText("Edit take_screenshot")
  ).toBeInTheDocument();
  expect(
    screen.getByLabelText("Delete take_screenshot")
  ).toBeInTheDocument();
});

test("Ctrl+K focuses the search input", async () => {
  renderPage();
  await screen.findByText("take_screenshot");
  const input = screen.getByLabelText("Search commands");
  expect(document.activeElement).not.toBe(input);
  fireEvent.keyDown(window, { key: "k", ctrlKey: true });
  expect(document.activeElement).toBe(input);
});

test("respects prefers-reduced-motion: reduce on the row cascade", async () => {
  mockReducedMotion(true);
  renderPage();

  await screen.findByText("take_screenshot");

  const rows = document.querySelectorAll("[data-reduced-motion]");
  expect(rows.length).toBeGreaterThan(0);

  rows.forEach((row) => {
    expect(row.getAttribute("data-reduced-motion")).toBe("true");
    const style = (row as HTMLElement).style;
    expect(style.transform === "" || style.transform === "none").toBe(true);
    expect(style.opacity === "" || style.opacity === "1").toBe(true);
    expect(style.transitionDelay).toBe("");
  });
});

test("applies the staggered cascade when motion is allowed", async () => {
  mockReducedMotion(false);
  renderPage();

  await screen.findByText("take_screenshot");

  const rows = document.querySelectorAll("[data-reduced-motion]");
  expect(rows.length).toBeGreaterThan(0);
  rows.forEach((row) => {
    expect(row.getAttribute("data-reduced-motion")).toBe("false");
  });
});

test("JSON import shows a confirm dialog with a diff before applying", async () => {
  renderPage();
  await screen.findByText("take_screenshot");

  // open_docs is removed, new_cmd is added in the imported file.
  const importContent = JSON.stringify({
    take_screenshot: { action: "keypress", keys: "alt+print_screen" },
    new_cmd: { action: "url", url: "https://new.example" },
  });
  const file = new File([importContent], "commands.json", {
    type: "application/json",
  });

  const fileInput = document.querySelector(
    'input[type="file"]'
  ) as HTMLInputElement;
  fireEvent.change(fileInput, { target: { files: [file] } });

  // Diff badges should appear and updateConfig must NOT have been called yet.
  expect(await screen.findByText("+1 added")).toBeInTheDocument();
  expect(screen.getByText("-1 removed")).toBeInTheDocument();
  expect(apiService.updateConfig).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: /Apply Import/ }));
  await waitFor(() => {
    expect(apiService.updateConfig).toHaveBeenCalledWith({
      commands: {
        take_screenshot: { action: "keypress", keys: "alt+print_screen" },
        new_cmd: { action: "url", url: "https://new.example" },
      },
    });
  });
});
