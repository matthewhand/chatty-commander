import { test, expect } from "@playwright/test";

test.describe("Commands Page Mock Verification", () => {
    test("commands page should display real config data and not mock data", async ({ page }) => {
        await page.goto("/commands");

        // Wait for page to load
        // Use a more specific locator to avoid strict mode violation
        await expect(page.getByRole('heading', { name: "Commands & Triggers" })).toBeVisible();

        // Assert absence of Mock Data
        await expect(page.getByText("Turn On Lights", { exact: true })).not.toBeVisible();
        await expect(page.getByText("Stop/Cancel", { exact: true })).not.toBeVisible();
        await expect(page.getByText("home_assistant_script")).not.toBeVisible();

        // Assert presence of Real Config Data. Commands now render as table rows
        // (Wave-2 refactor), so command names are table cells, not headings.
        // "take_screenshot" is a key in the default config.json
        await expect(page.getByRole('cell', { name: "take_screenshot", exact: true })).toBeVisible();

        // "cycle_window" is another default command
        await expect(page.getByRole('cell', { name: "cycle_window", exact: true })).toBeVisible();
    });
});
