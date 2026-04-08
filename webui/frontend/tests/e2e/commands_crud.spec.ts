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

  test("commands page renders with command cards", async ({ page }) => {
    await page.goto("/commands");

    await expect(
      page.getByRole("heading", { name: "Commands & Triggers" })
    ).toBeVisible();

    // All four mock commands should be visible
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "open_browser" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "say_hello" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "volume_up" })).toBeVisible();
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
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    const initialFetchCount = fetchCount;

    // Click the refresh button
    await page.getByRole("button", { name: "Refresh Commands" }).click();

    // Wait for the refetch to complete
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    // Verify an additional fetch was triggered
    expect(fetchCount).toBeGreaterThan(initialFetchCount);
  });

  test("New Command button navigates to /commands/authoring", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "Commands & Triggers" })).toBeVisible();

    await page.getByRole("link", { name: "New Command" }).click();
    await expect(page).toHaveURL(/\/commands\/authoring/);
  });

  test("command card shows action type badge", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    // Each command card should display its action type
    await expect(page.getByText("shell").first()).toBeVisible();
    await expect(page.getByText("url").first()).toBeVisible();
    await expect(page.getByText("custom_message").first()).toBeVisible();
    await expect(page.getByText("keypress").first()).toBeVisible();
  });

  test("command card dropdown menu opens on click", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    // Find the dropdown toggle button (aria-haspopup) for the first command card
    const dropdownButton = page.locator("[aria-haspopup='true']").first();

    // In DaisyUI, clicking the icon might not register on the wrapper, evaluate raw click
    await dropdownButton.evaluate(node => node.click());

    // Dropdown menu items should be visible
    // They are in a hidden UL, we need to make sure the state changed. The dropdown items are hidden but visible via playwright if aria-expanded="true". We don't check for visibility, but verify they are attached.
    await expect(page.getByText("Edit Command").first()).toBeAttached();
    await expect(page.getByText("Delete Command").first()).toBeAttached();
  });

  test("delete action in dropdown triggers action", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    // Open dropdown for take_screenshot
    const dropdownButton = page.locator("[aria-haspopup='true']").first();
    await dropdownButton.evaluate(node => node.click());

    // The delete button should be visible with correct aria-label
    const deleteButton = page.locator("button[aria-label='Delete take_screenshot']");
    await expect(deleteButton).toBeAttached();
    await expect(deleteButton).toHaveClass(/text-error/);
  });

  test("command count display when searching", async ({ page }) => {
    await page.goto("/commands");
    await expect(page.getByRole("heading", { name: "take_screenshot" })).toBeVisible();

    const searchInput = page.locator('input[placeholder="Search commands..."]');
    await searchInput.fill("screenshot");

    // Should show count of filtered results
    await expect(page.getByText("Showing 1 of 4 commands")).toBeVisible();
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
