import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
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

function renderPage(initialEntries: string[] = ["/commands"]) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <CommandsPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

// The page renders the same commands twice: a desktop <table> (hidden below md)
// and a mobile card <ul aria-label="Commands"> (hidden at md+). jsdom applies no
// CSS, so both are present in the DOM. These helpers scope queries to one of the
// two so assertions stay unambiguous.
function getTable() {
  return screen.getByRole("table");
}
function getCardList() {
  return screen.getByRole("list", { name: "Commands" });
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
  await screen.findAllByText("take_screenshot");
  const table = within(getTable());
  expect(table.getByText("take_screenshot")).toBeInTheDocument();
  expect(table.getByText("open_docs")).toBeInTheDocument();
});

test("each row describes the command's actual action", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");
  const table = within(getTable());
  // keypress command shows the keys it presses
  expect(table.getByText("Presses keys")).toBeInTheDocument();
  expect(table.getByText("alt+print_screen")).toBeInTheDocument();
  // url command shows the URL it opens
  expect(table.getByText("Opens URL")).toBeInTheDocument();
  expect(table.getByText("https://example.com/docs")).toBeInTheDocument();
});

test("renders a distinct type badge per command type", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");
  const table = within(getTable());
  // keypress -> "Keypress" badge, url -> "URL" badge (not the same label).
  expect(table.getByText("Keypress")).toBeInTheDocument();
  expect(table.getByText("URL")).toBeInTheDocument();
});

test("infers the type from the payload when action is missing", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    run_thing: { cmd: "echo hi" },
    say_hi: { message: "hello there" },
  });
  renderPage();
  await screen.findAllByText("run_thing");
  const table = within(getTable());
  expect(table.getByText("Shell")).toBeInTheDocument();
  expect(table.getByText("Message")).toBeInTheDocument();
});

test("default sort is alphabetical by name", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    zeta: { action: "url", url: "https://z.example" },
    alpha: { action: "url", url: "https://a.example" },
  });
  renderPage();
  await screen.findAllByText("alpha");
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
  await screen.findAllByText("aaa_url");
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
  await screen.findAllByText("take_screenshot");
  fireEvent.change(screen.getByLabelText("Search commands"), {
    target: { value: "print_screen" },
  });
  // Only the keypress command (whose detail contains print_screen) should remain.
  // It appears in both the table and the mobile card list, so assert on the table.
  await waitFor(() => {
    const table = within(getTable());
    expect(table.getByText("take_screenshot")).toBeInTheDocument();
    expect(table.queryByText("open_docs")).not.toBeInTheDocument();
  });
});

test("delete failure surfaces a toast instead of window.alert", async () => {
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
  (apiService.deleteCommand as ReturnType<typeof vi.fn>).mockRejectedValue(
    new Error("boom")
  );
  renderPage();
  await screen.findAllByText("take_screenshot");

  // Use the table's delete control (there is also a mobile-card equivalent).
  fireEvent.click(
    within(getTable()).getByLabelText("Delete take_screenshot")
  );
  fireEvent.click(screen.getByRole("button", { name: "Delete" }));

  const toast = await screen.findByText(/Failed to delete command: boom/);
  expect(toast).toBeInTheDocument();
  expect(alertSpy).not.toHaveBeenCalled();
  alertSpy.mockRestore();
});

test("each row exposes direct Edit and Delete controls", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");
  const table = within(getTable());
  expect(table.getByLabelText("Edit take_screenshot")).toBeInTheDocument();
  expect(table.getByLabelText("Delete take_screenshot")).toBeInTheDocument();
});

test("Ctrl+K focuses the search input", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");
  const input = screen.getByLabelText("Search commands");
  expect(document.activeElement).not.toBe(input);
  fireEvent.keyDown(window, { key: "k", ctrlKey: true });
  expect(document.activeElement).toBe(input);
});

test("respects prefers-reduced-motion: reduce on the row cascade", async () => {
  mockReducedMotion(true);
  renderPage();

  await screen.findAllByText("take_screenshot");

  // Scope to table rows so the assertion is over a single, known set.
  const rows = getTable().querySelectorAll("[data-reduced-motion]");
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

  await screen.findAllByText("take_screenshot");

  const rows = getTable().querySelectorAll("[data-reduced-motion]");
  expect(rows.length).toBeGreaterThan(0);
  rows.forEach((row) => {
    expect(row.getAttribute("data-reduced-motion")).toBe("false");
  });
});

test("JSON import shows a confirm dialog with a diff before applying", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");

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

// --- Mobile card list (md:hidden fallback for the table) -------------------

test("renders a mobile card list mirroring the table's commands + actions", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");

  const cards = within(getCardList());
  // Same names appear in the card list.
  expect(cards.getByText("take_screenshot")).toBeInTheDocument();
  expect(cards.getByText("open_docs")).toBeInTheDocument();
  // Each card exposes Edit / Delete / Test with the same accessible labels.
  expect(cards.getByLabelText("Edit take_screenshot")).toBeInTheDocument();
  expect(cards.getByLabelText("Delete take_screenshot")).toBeInTheDocument();
  expect(cards.getByLabelText("Test take_screenshot")).toBeInTheDocument();
});

test("mobile card delete control opens the same confirm dialog", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");

  fireEvent.click(
    within(getCardList()).getByLabelText("Delete take_screenshot")
  );
  // The shared confirmation dialog appears.
  expect(
    screen.getByRole("button", { name: "Delete" })
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Delete" }));
  await waitFor(() => {
    expect(apiService.deleteCommand).toHaveBeenCalledWith("take_screenshot");
  });
});

// --- Sortable headers with aria-sort ---------------------------------------

test("column headers expose aria-sort and toggle via header buttons", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    aaa_url: { action: "url", url: "https://a.example" },
    bbb_key: { action: "keypress", keys: "ctrl+a" },
  });
  renderPage();
  await screen.findAllByText("aaa_url");

  const nameHeader = screen.getByRole("columnheader", { name: /Name/ });
  const typeHeader = screen.getByRole("columnheader", { name: /Type/ });
  // Default: sorted ascending by name.
  expect(nameHeader).toHaveAttribute("aria-sort", "ascending");
  expect(typeHeader).toHaveAttribute("aria-sort", "none");

  // Clicking the Name header again toggles to descending.
  fireEvent.click(within(nameHeader).getByRole("button"));
  await waitFor(() => {
    expect(
      screen.getByRole("columnheader", { name: /Name/ })
    ).toHaveAttribute("aria-sort", "descending");
  });

  // Order should now be reversed (zeta-style: bbb before aaa).
  const rows = document.querySelectorAll("tbody tr");
  const names = Array.from(rows).map(
    (r) => r.querySelector("td")?.textContent?.trim()
  );
  expect(names).toEqual(["bbb_key", "aaa_url"]);

  // Clicking the Type header switches the active sort key.
  fireEvent.click(
    within(screen.getByRole("columnheader", { name: /Type/ })).getByRole("button")
  );
  await waitFor(() => {
    expect(
      screen.getByRole("columnheader", { name: /Type/ })
    ).toHaveAttribute("aria-sort", "ascending");
    expect(
      screen.getByRole("columnheader", { name: /Name/ })
    ).toHaveAttribute("aria-sort", "none");
  });
});

test("sort key is persisted in the URL search params", async () => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    aaa_url: { action: "url", url: "https://a.example" },
    bbb_key: { action: "keypress", keys: "ctrl+a" },
  });
  // Start with ?sort=type already in the URL — it should take effect on load.
  renderPage(["/commands?sort=type"]);
  await screen.findAllByText("aaa_url");
  // Keypress < URL, so bbb_key sorts first when grouped by type.
  await waitFor(() => {
    const rows = document.querySelectorAll("tbody tr");
    const names = Array.from(rows).map(
      (r) => r.querySelector("td")?.textContent?.trim()
    );
    expect(names).toEqual(["bbb_key", "aaa_url"]);
  });
  expect(
    screen.getByRole("columnheader", { name: /Type/ })
  ).toHaveAttribute("aria-sort", "ascending");
});

// --- aria-live result count -------------------------------------------------

test("the filtered result count is announced via aria-live", async () => {
  renderPage();
  await screen.findAllByText("take_screenshot");
  fireEvent.change(screen.getByLabelText("Search commands"), {
    target: { value: "print_screen" },
  });
  const count = await screen.findByText(/Showing \d+ of \d+ commands/);
  expect(count).toHaveAttribute("aria-live", "polite");
  await waitFor(() => {
    expect(count).toHaveTextContent("Showing 1 of 2 commands");
  });
});
