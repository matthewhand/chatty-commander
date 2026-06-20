import { test, expect } from "@playwright/test";

const MOCK_COMMANDS = {
  take_screenshot: {
    action: "shell",
    keys: null,
    url: null,
    cmd: "gnome-screenshot",
    message: null,
  },
  open_browser: {
    action: "url",
    keys: null,
    url: "https://example.com",
    cmd: null,
    message: null,
  },
  say_hello: {
    action: "custom_message",
    keys: null,
    url: null,
    cmd: null,
    message: "Hello there!",
  },
  volume_up: {
    action: "keypress",
    keys: "XF86AudioRaiseVolume",
    url: null,
    cmd: null,
    message: null,
  },
};

test.describe("Commands Page CRUD", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/commands", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_COMMANDS),
        });
      } else {
        await route.continue();
      }
    });
  });

  test("commands page renders with command rows", async ({ page }) => {
    await page.goto("/commands");

    await expect(
      page.getByRole("heading", { name: "Commands & Triggers" })
    ).toBeVisible();

    // The 2-up card grid is now a table; each command is a row whose Name
    // cell holds the command name.
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "open_browser", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "say_hello", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "volume_up", exact: true })).toBeVisible();

    // Search input + scoped type badge on a row.
    await expect(page.getByPlaceholder("Search commands...")).toBeVisible();
    await expect(
      page.getByRole("row", { name: /take_screenshot/ }).locator(".badge", { hasText: "Shell" })
    ).toBeVisible();

    await expect(page.getByRole("link", { name: "New Command" })).toBeVisible();
  });

  test("refresh button triggers API refetch", async ({ page }) => {
    let fetchCount = 0;
    await page.route("**/api/v1/commands", async (route) => {
      fetchCount++;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_COMMANDS),
      });
    });

    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    const initialFetchCount = fetchCount;

    // Click the refresh button
    await page.getByRole("button", { name: "Refresh Commands" }).click();

    // Wait for the refetch to complete
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    // Verify an additional fetch was triggered
    expect(fetchCount).toBeGreaterThan(initialFetchCount);
  });

  test("New Command button navigates to /commands/authoring", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "Commands & Triggers" })).toBeVisible();

    await page.getByRole("link", { name: "New Command" }).click();
    await expect(page).toHaveURL(/\/commands\/authoring/);
  });

  test("command row shows action type badge", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    // Each command row displays a colored .badge with its human-readable type
    // label (Shell / URL / Message / Keypress), scoped to its row. Target the
    // badge specifically so it doesn't collide with the action-detail text
    // (e.g. "Opens URL").
    await expect(page.getByRole("row", { name: /take_screenshot/ }).locator(".badge", { hasText: "Shell" })).toBeVisible();
    await expect(page.getByRole("row", { name: /open_browser/ }).locator(".badge", { hasText: "URL" })).toBeVisible();
    await expect(page.getByRole("row", { name: /say_hello/ }).locator(".badge", { hasText: "Message" })).toBeVisible();
    await expect(page.getByRole("row", { name: /volume_up/ }).locator(".badge", { hasText: "Keypress" })).toBeVisible();
  });

  test("each row exposes direct Edit and Delete controls", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    // Edit is now a direct link to the authoring page (not behind a dropdown).
    const editLink = page.getByRole("link", { name: "Edit take_screenshot" });
    await expect(editLink).toBeVisible();
    await expect(editLink).toHaveAttribute(
      "href",
      /\/commands\/authoring\?edit=take_screenshot/
    );

    // Delete is a direct icon button.
    const deleteButton = page.getByRole("button", { name: "Delete take_screenshot" });
    await expect(deleteButton).toBeVisible();
    await expect(deleteButton).toHaveClass(/text-error/);
  });

  test("row dropdown holds the 'Test this command' link", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    // The per-row dropdown now only contains "Test this command". Scope to the
    // button role: the open menu panel shares the same aria-label.
    const dropdownButton = page.getByRole("button", { name: "More options for take_screenshot" });
    await expect(dropdownButton).toHaveAttribute("aria-expanded", "false");

    await dropdownButton.click();
    await expect(dropdownButton).toHaveAttribute("aria-expanded", "true");

    const testLink = page.getByRole("menuitem", { name: "Test take_screenshot" });
    await expect(testLink).toBeVisible();
    await expect(testLink).toHaveAttribute(
      "href",
      /\/voice-test\?command=take_screenshot/
    );
  });

  test("delete button opens the confirmation dialog", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Delete take_screenshot" }).click();

    // A confirm-deletion modal appears naming the command.
    const dialog = page.locator("dialog.modal[open]");
    await expect(dialog.getByRole("heading", { name: "Confirm Deletion" })).toBeVisible();
    await expect(dialog.getByText("take_screenshot")).toBeVisible();
  });

  test("command count display when searching", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("cell", { name: "take_screenshot", exact: true })).toBeVisible();

    const searchInput = page.locator('input[placeholder="Search commands..."]');
    await searchInput.fill("screenshot");

    // Should show count of filtered results (use regex to avoid brittle exact count/text if mock or UI text changes)
    await expect(page.getByText(/Showing .* of .* commands/)).toBeVisible();
  });
});

test.describe("Commands Page - Empty State", () => {
  test("shows empty state when no commands exist", async ({ page }) => {
    await page.route("**/api/v1/commands", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({}),
      });
    });

    await page.goto("/commands");

    await expect(
      page.getByRole("heading", { name: "Commands & Triggers" })
    ).toBeVisible();

    await expect(page.getByRole('heading', { name: "No commands configured." })).toBeVisible();
  });
});
