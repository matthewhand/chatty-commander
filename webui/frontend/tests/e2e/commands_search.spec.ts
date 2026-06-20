import { test, expect } from "@playwright/test";

test.describe("Commands Page Search Synchronization", () => {
  test("Search query updates URL parameter and filters commands", async ({ page }) => {
    // We mock the API response for commands to be deterministic
    await page.route('**/api/v1/commands', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          "Take Screenshot": {
            "action": "shell",
            "keys": null,
            "url": null,
            "cmd": "gnome-screenshot",
            "message": null
          },
          "Hello World": {
            "action": "custom_message",
            "keys": null,
            "url": null,
            "cmd": null,
            "message": "Hello, User!"
          }
        })
      });
    });

    await page.goto("/commands");

    // The card grid is now a `table table-zebra`; assert on rows. Each command's
    // name lives in a table cell, so target the cell role rather than free text.
    const screenshotRow = page.getByRole("row", { name: /Take Screenshot/ });
    const helloRow = page.getByRole("row", { name: /Hello World/ });
    await expect(page.getByRole("cell", { name: "Take Screenshot", exact: true })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Hello World", exact: true })).toBeVisible();

    // Type in search bar
    const searchInput = page.getByPlaceholder("Search commands...");
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEnabled();
    await searchInput.fill("Screenshot");

    // URL should be updated with ?q=Screenshot
    await expect(page).toHaveURL(/.*q=Screenshot/);

    // Filtering removes the non-matching row entirely (debounced ~300ms).
    await expect(screenshotRow).toBeVisible();
    await expect(helloRow).toHaveCount(0);

    // The "Showing N of M commands" count appears while a search is active.
    await expect(page.getByText(/Showing .* of .* commands/)).toBeVisible();

    // Clear search bar
    await searchInput.fill("");

    // URL should drop the search query
    await expect(page).not.toHaveURL(/.*q=/);

    // All rows should be visible again
    await expect(screenshotRow).toBeVisible();
    await expect(helloRow).toBeVisible();

    // Navigate to page with pre-filled query
    await page.goto("/commands?q=Hello");

    // Search bar should be populated from URL
    await expect(searchInput).toHaveValue("Hello");

    // Results should be pre-filtered
    await expect(page.getByRole("row", { name: /Take Screenshot/ })).toHaveCount(0);
    await expect(page.getByRole("cell", { name: "Hello World", exact: true })).toBeVisible();

    // +2 wired endpoint asserts (via request; hits mocks/server per WEBUI/ROADMAP e2e expansion)
    const cmdsRes = await page.request.get("/api/v1/commands");
    expect(cmdsRes.ok()).toBeTruthy();
    const healthRes = await page.request.get("/health");
    expect(healthRes.ok()).toBeTruthy();
  });
});
