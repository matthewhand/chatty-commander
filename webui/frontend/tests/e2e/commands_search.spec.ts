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

    // Wait for commands to load
    await expect(page.locator("text=Take Screenshot").first()).toBeVisible();
    await expect(page.locator("text=Hello World").first()).toBeVisible();

    // Type in search bar
    const searchInput = page.locator('input[placeholder="Search commands..."]');
    await searchInput.fill("Screenshot");

    // URL should be updated with ?q=Screenshot
    await expect(page).toHaveURL(/.*q=Screenshot/);

    // Results should be filtered
    await expect(page.locator("text=Take Screenshot").first()).toBeVisible();
    await expect(page.locator("text=Hello World")).not.toBeVisible();

    // Clear search bar
    await searchInput.fill("");

    // URL should drop the search query
    await expect(page).not.toHaveURL(/.*q=/);

    // All results should be visible again
    await expect(page.locator("text=Take Screenshot").first()).toBeVisible();
    await expect(page.locator("text=Hello World").first()).toBeVisible();

    // Navigate to page with pre-filled query
    await page.goto("/commands?q=Hello");

    // Search bar should be populated from URL
    await expect(searchInput).toHaveValue("Hello");

    // Results should be pre-filtered
    await expect(page.locator("text=Take Screenshot")).not.toBeVisible();
    await expect(page.locator("text=Hello World").first()).toBeVisible();
  });
});
