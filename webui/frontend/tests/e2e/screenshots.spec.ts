import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

// Fix for ES modules not having __dirname
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

        // Wait for connection to settle or force enable elements
        await page.waitForTimeout(1000);

        // Mock WebSocket connection state if not connected
        const isConnected = await page.evaluate(() => {
            const input = document.querySelector('input[placeholder="Type a command to execute..."]') as HTMLInputElement;
            return input && !input.disabled;
        });

        if (!isConnected) {
             // Force enable UI elements for screenshot purpose if WS failed
            await page.evaluate(() => {
                const input = document.querySelector('input[placeholder="Type a command to execute..."]') as HTMLInputElement;
                const button = document.querySelector('button[type="submit"]') as HTMLButtonElement;
                if (input) {
                    input.disabled = false;
                    input.classList.remove('disabled'); // Remove tailwind disabled classes if any
                }
                if (button) {
                    button.disabled = false;
                    button.classList.remove('btn-disabled');
                }
            });
        }

        // Simulate user interaction to populate logs
        const input = page.getByPlaceholder("Type a command to execute...");
        // Ensure input is actionable
        await input.fill("help", { force: true });

        const button = page.locator("button:has-text('Execute')");
        // Ensure button is actionable
        await button.click({ force: true });

        // Wait for log entry to appear
        // If the backend isn't actually processing, we might need to manually inject a log entry
        // for the screenshot to look correct if the optimisitc update relies on something that failed.
        // But the current code does optimistic update before sending.
        try {
            await expect(page.locator("text=Executing: help")).toBeVisible({ timeout: 5000 });
        } catch (e) {
            // Fallback: manually inject log entry if optimistic update didn't render or backend failed hard
            await page.evaluate(() => {
                const logContainer = document.querySelector('.mockup-code');
                if (logContainer) {
                   const div = document.createElement('div');
                   div.className = "px-4 py-1 hover:bg-base-content/5 flex gap-2 font-mono text-sm";
                   div.innerHTML = `<span class="opacity-50 select-none">[12:00:00 PM]</span><span class="text-info">> Executing: help</span>`;
                   logContainer.appendChild(div);
                }
            });
        }

        await page.waitForTimeout(500); // Allow render to settle

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
        const commandsLink = page.locator("text=Commands").first();
        if (await commandsLink.isVisible()) {
            await commandsLink.click();
            await page.waitForTimeout(500);
        }
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "commands.png"), fullPage: true });
    });
});
