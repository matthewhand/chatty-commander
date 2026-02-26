import { test, expect } from "@playwright/test";
import path from "path";

// Relative path from webui/frontend to docs/images
const ARTIFACTS_DIR = "../../docs/images";

test.describe("UI Screenshots", () => {
    test("capture all pages", async ({ page }) => {
        // 1. Dashboard
        await page.goto("/");
        // Wait for stats to load
        await page.waitForSelector(".stats", { timeout: 5000 }).catch(() => { });
        await page.waitForTimeout(1000); // Allow animations/graphs to settle
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "dashboard.png"), fullPage: true });

        // 2. Configuration
        await page.click("text=Configuration");
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "configuration.png"), fullPage: true });

        // 6. Login Page (Fake logout)
        // We can't easily logout with NO_AUTH=true, so let's just go to /login explicitly
        await page.goto("/login");
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "login.png"), fullPage: true });
    });
});
