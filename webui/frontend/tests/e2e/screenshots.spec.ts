import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

// Assuming we run from webui/frontend
const ARTIFACTS_DIR = path.resolve(process.cwd(), "../../docs/images");

test.describe("UI Screenshots", () => {
    test.beforeAll(async () => {
        if (!fs.existsSync(ARTIFACTS_DIR)) {
            fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
        }
    });

    test("capture all pages", async ({ page }) => {
        // 1. Dashboard
        await page.goto("/");
        await expect(page).toHaveURL(/dashboard/);
        // Wait for stats to load
        await page.waitForSelector(".stats");
        await page.waitForTimeout(2000); // Allow animations/graphs to settle
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "dashboard.png"), fullPage: true });

        // 2. Configuration
        await page.goto("/configuration");
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(1000);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "configuration.png"), fullPage: true });

        // 3. Commands
        await page.goto("/commands");
        await expect(page).toHaveURL(/commands/);
        await page.waitForTimeout(1000);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "commands.png"), fullPage: true });

        // 4. Login Page (if accessible via direct URL even when authenticated? probably redirects)
        // await page.goto("/login");
        // await page.waitForTimeout(1000);
        // await page.screenshot({ path: path.join(ARTIFACTS_DIR, "login.png"), fullPage: true });
    });
});
