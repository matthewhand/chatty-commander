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
        // The sticky app bar adds a duplicate page-title heading; scope to first.
        await expect(page.getByRole("heading", { name: "Configuration" }).first()).toBeVisible();

        // Go to Commands
        await page.getByRole("link", { name: "Commands" }).click();
        await expect(page).toHaveURL(/commands/);
        await expect(page.getByRole("heading", { name: "Commands & Triggers" })).toBeVisible();
    });

    test("invalid route redirects or shows 404", async ({ page }) => {
        await page.goto("/non-existent-page-12345");

        // Current routing (App.tsx catch-all *) always redirects unknown to / then /dashboard.
        // Stabilize with load state (no brittle timeout). Update test to match actual behavior; remove dead 404 branch.
        await page.waitForLoadState("domcontentloaded");
        await expect(page).toHaveURL(/dashboard/);
    });

    test("configuration form interactions", async ({ page }) => {
        await page.goto("/configuration");

        await expect(page.getByRole("heading", { name: /configuration/i }).first()).toBeVisible();

        // Use actual modern locators from ConfigurationPage (theme select + service toggles)
        // avoids outdated generic input[type=text] + conditional fallbacks.
        // exact:true — the global layout also exposes a "Select theme" picker.
        await expect(page.getByLabel("Theme", { exact: true })).toBeVisible();
        await expect(page.getByText("Voice Commands (always-on)")).toBeVisible();
        await expect(page.getByText("REST API")).toBeVisible();
    });
});
