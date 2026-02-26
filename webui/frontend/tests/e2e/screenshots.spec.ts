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

        // 2. Configuration
        await page.click("text=Configuration");
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "configuration.png"), fullPage: true });

        // 3. Audio Settings
        await page.click("text=Audio Settings");
        await expect(page).toHaveURL(/audio-settings/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "audio_settings.png"), fullPage: true });

        // 4. Personas
        await page.click("text=Personas");
        await expect(page).toHaveURL(/personas/);
        // Wait for persona cards to render (or timeout gracefully)
        await page.waitForSelector(".card", { timeout: 5000 }).catch(() => { });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "personas.png"), fullPage: true });

        // 5. Agent Status
        await page.click("text=Agent Status");
        await expect(page).toHaveURL(/agent-status/);
        // Wait for agent cards to render (or timeout gracefully)
        await page.waitForSelector(".card", { timeout: 5000 }).catch(() => { });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "agent_status.png"), fullPage: true });

        // 6. Login Page (Fake logout)
        // We can't easily logout with NO_AUTH=true, so let's just go to /login explicitly
        await page.goto("/login");
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(ARTIFACTS_DIR, "login.png"), fullPage: true });
    });
});
