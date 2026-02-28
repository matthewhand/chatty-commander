import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");

test.describe("Documentation Screenshots", () => {
    test.beforeAll(() => {
        fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
    });

    test("dashboard", async ({ page }) => {
        await page.goto("/");
        await expect(page).toHaveURL(/dashboard/);
        await page.waitForTimeout(1500);
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "dashboard.png"), fullPage: true });
    });

    test("login", async ({ page }) => {
        await page.goto("/login");
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "login.png"), fullPage: true });
    });

    test("configuration-general", async ({ page }) => {
        await page.goto("/");
        await page.click("text=Configuration");
        await expect(page).toHaveURL(/configuration/);
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "configuration-general.png"), fullPage: true });
    });

    test("configuration-llm", async ({ page }) => {
        await page.goto("/");
        await page.click("text=Configuration");
        await page.waitForTimeout(300);
        const llmTab = page.locator("text=LLM").first();
        if (await llmTab.isVisible()) {
            await llmTab.click();
            await page.waitForTimeout(300);
        }
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "configuration-llm.png"), fullPage: true });
    });

    test("configuration-services", async ({ page }) => {
        await page.goto("/");
        await page.click("text=Configuration");
        await page.waitForTimeout(300);
        const servicesTab = page.locator("text=Services").first();
        if (await servicesTab.isVisible()) {
            await servicesTab.click();
            await page.waitForTimeout(300);
        }
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "configuration-services.png"), fullPage: true });
    });

    test("commands", async ({ page }) => {
        await page.goto("/");
        const commandsLink = page.getByRole('link', { name: "Commands" }).first();
        if (await commandsLink.isVisible()) {
            await commandsLink.click();
            await page.waitForTimeout(500);
        }
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "commands.png"), fullPage: true });
    });
});
