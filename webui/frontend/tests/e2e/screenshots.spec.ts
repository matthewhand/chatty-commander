import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Resolve path relative to the project root
// tests/e2e/screenshots.spec.ts -> ../../../docs/images
const ARTIFACTS_DIR = path.resolve(__dirname, "../../../../docs/images");

test.describe("UI Screenshots", () => {
    test.beforeAll(async () => {
        if (!fs.existsSync(ARTIFACTS_DIR)) {
            fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
        }
    });

    test("capture all pages", async ({ page }) => {
        // 1. Dashboard
        await page.goto("/");
        // Wait for stats to load (they come from /health endpoint)
        await page.waitForTimeout(2000);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "dashboard.png"), fullPage: true });

        // 2. Configuration
        // Check if navigation link exists, otherwise try direct navigation
        try {
            await page.click("text=Configuration");
        } catch {
            await page.goto("/configuration");
        }
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(1000);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "configuration.png"), fullPage: true });
    });
});
