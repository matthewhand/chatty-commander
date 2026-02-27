import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");

const MOCK_COMMANDS = [
    {
        "id": "cmd_lights_on",
        "displayName": "Turn On Lights",
        "actionType": "home_assistant_script",
        "payload": "script.lights_on",
        "apiEnabled": true,
        "wakewords": [
            {
                "id": "ww_lights_on_1",
                "displayName": "Lights On",
                "isActive": true,
                "threshold": 0.5,
                "assets": ["models/lights_on.onnx"]
            }
        ]
    },
    {
        "id": "cmd_stop",
        "displayName": "Stop/Cancel",
        "actionType": "system_interrupt",
        "payload": "cancel_current",
        "apiEnabled": true,
        "wakewords": [
            {
                "id": "ww_stop_1",
                "displayName": "Okay Stop",
                "isActive": true,
                "threshold": 0.4,
                "assets": ["models/okay_stop.onnx"]
            }
        ]
    }
];

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
        // Mock the backend API response for commands page
        await page.route('**/api/v1/commands', async route => {
            await route.fulfill({ json: MOCK_COMMANDS });
        });

        await page.goto("/");
        const commandsLink = page.locator("text=Commands").first();
        if (await commandsLink.isVisible()) {
            await commandsLink.click();
            await page.waitForTimeout(1500); // Allow for animation/loading
        }
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, "commands.png"), fullPage: true });
    });
});
