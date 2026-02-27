import { test, expect } from "@playwright/test";

test.describe("Commands Page Verification", () => {
    test("commands are loaded from backend", async ({ page }) => {
        await page.goto("/commands");
        await expect(page).toHaveURL(/commands/);

        // Wait for network idle to ensure requests are complete
        await page.waitForLoadState('networkidle');

        // Assert that the default command "lights_on" (from config.json) is visible as a heading
        // Use a more specific locator to avoid strict mode violations (since the text might appear in the URL payload too)
        await expect(page.locator("h2", { hasText: "lights_on" })).toBeVisible();

        // Assert that the mock command "Turn On Lights" is NOT visible
        await expect(page.locator("text=Turn On Lights")).not.toBeVisible();
    });
});
