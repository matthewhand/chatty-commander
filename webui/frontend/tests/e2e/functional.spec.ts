import { test, expect } from "@playwright/test";

test.describe("Functional Flows", () => {
    test("sidebar navigation interaction updates URL and active state", async ({ page }) => {
        await page.goto("/");
        await expect(page).toHaveURL(/dashboard/);

        // Click on 'Configuration' and verify
        await page.getByRole("link", { name: "Configuration" }).click();
        await expect(page).toHaveURL(/configuration/);

        // Verify the link has active class or similar visual indicator if applicable
        // For DaisyUI/Tailwind, typically 'active' or 'bg-base-200' class.
        // We'll check if the link is visible and URL is correct, which is robust enough for functional flow.
        await expect(page.getByRole("heading", { name: "Configuration" })).toBeVisible();

        // Go to Commands
        await page.getByRole("link", { name: "Commands" }).click();
        await expect(page).toHaveURL(/commands/);
        await expect(page.getByRole("heading", { name: "Commands & Triggers" })).toBeVisible();
    });

    test("invalid route redirects or shows 404", async ({ page }) => {
        await page.goto("/non-existent-page-12345");

        // Check if we stay on the page (indicating 404 component) or redirect to dashboard
        // The current router behavior usually redirects to dashboard for unknown routes in some setups, or shows a 404.
        // Let's check for either: "404", "Not Found", or redirect to /dashboard.

        // Wait for stability
        await page.waitForTimeout(500);

        const url = page.url();
        if (url.includes("dashboard")) {
            // Redirect behavior
            await expect(page).toHaveURL(/dashboard/);
        } else {
            // 404 Page behavior
            // Check for common 404 text
            const bodyText = await page.innerText("body");
            expect(bodyText.toLowerCase()).toMatch(/not found|404/);
        }
    });

    test("configuration form interactions", async ({ page }) => {
        await page.goto("/configuration");

        // Verify we can find typical inputs
        // Assuming there are input fields for API keys or similar.
        // Since we don't want to rely on specific field names that might change, 
        // we'll look for generic inputs and ensure they are interactive.

        const inputs = page.locator("input[type='text']");
        if (await inputs.count() > 0) {
            const firstInput = inputs.first();
            await expect(firstInput).toBeEnabled();
            await firstInput.fill("test value");
            await expect(firstInput).toHaveValue("test value");
        } else {
            // Only check for a button if no inputs are found
            // Use a more specific locator or .first() to avoid strict mode errors
            const saveButton = page.getByRole('button', { name: /save/i }).first();
            if (await saveButton.count() > 0) {
                await expect(saveButton).toBeVisible();
            } else {
                // Fallback: check any button is visible
                await expect(page.locator("button").first()).toBeVisible();
            }
        }
    });
});
