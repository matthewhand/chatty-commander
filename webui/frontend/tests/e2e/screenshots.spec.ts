import { test, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ARTIFACTS_DIR = path.resolve(__dirname, "../../../../docs/images");

test.describe("UI Screenshots", () => {
    test("capture all pages", async ({ page }) => {
        // 1. Dashboard
        await page.goto("/");
        await expect(page).toHaveURL(/dashboard/);
        await page.waitForTimeout(1000); // Allow animations/graphs to settle
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "dashboard.png"), fullPage: true });

        // 2. Commands
        // Note: The link text in MainLayout is "Commands"
        // Wait for potential navigation animations
        await page.click("text=Commands");
        await expect(page).toHaveURL(/commands/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "commands.png"), fullPage: true });

        // 3. Configuration
        await page.click("text=Configuration");
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "configuration.png"), fullPage: true });

        // 4. Login Page (Fake logout)
        // We can't easily logout with NO_AUTH=true, so let's just go to /login explicitly
        await page.goto("/login");
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "login.png"), fullPage: true });
    });
});
