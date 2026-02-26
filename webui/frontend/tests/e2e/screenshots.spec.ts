import { test, expect } from "@playwright/test";
import path from "path";

// Assuming running from webui/frontend/
const ARTIFACTS_DIR = path.resolve(process.cwd(), "../../docs/images");

test.describe("UI Screenshots", () => {
    test("capture dashboard", async ({ page }) => {
        // 1. Dashboard
        await page.goto("/");
        // Wait for redirect to /dashboard if applicable
        await page.waitForTimeout(2000);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "dashboard.png"), fullPage: true });
    });
});
