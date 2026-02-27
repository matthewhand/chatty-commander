import { test, expect } from "@playwright/test";

test.describe("Commands Page Data Source", () => {
    test("verify commands page shows real config", async ({ page }) => {
        // Navigate to the commands page
        await page.goto("/commands");

        // Wait for the page content to load
        await page.waitForTimeout(1000);

        // Check for the absence of mock data
        const mockCommand1 = page.locator("text=Turn On Lights");
        const mockCommand2 = page.locator("text=Stop/Cancel");

        await expect(mockCommand1).not.toBeVisible();
        await expect(mockCommand2).not.toBeVisible();

        // Check for the presence of real config data
        // The default config.json includes "take_screenshot"
        const realCommand = page.locator("text=take_screenshot");

        await expect(realCommand).toBeVisible();

        // --- Add New Command Test ---
        // Click New Command
        page.on('dialog', async dialog => {
             if (dialog.message().includes("command name")) {
                 await dialog.accept("test_cmd_123");
             } else if (dialog.message().includes("action type")) {
                 await dialog.accept("shell");
             } else if (dialog.message().includes("delete")) {
                 await dialog.accept();
             }
        });

        await page.click("text=New Command");

        // Wait for list update
        await page.waitForTimeout(1000);

        // Verify new command is visible
        const newCommand = page.locator("text=test_cmd_123");
        await expect(newCommand).toBeVisible();

        // --- Delete Command Test ---
        // Find the delete button for the new command
        // The card should contain the text "test_cmd_123"
        // We find the button within that context
        const deleteBtn = page.locator("button[aria-label='Delete test_cmd_123']");
        await deleteBtn.click();

        // Wait for list update
        await page.waitForTimeout(1000);

        // Verify command is gone
        await expect(newCommand).not.toBeVisible();
    });
});
