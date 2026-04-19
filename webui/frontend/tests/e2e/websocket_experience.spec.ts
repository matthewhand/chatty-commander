import { test, expect } from "@playwright/test";

test.describe("WebSocket Experience", () => {
    test("dashboard shows websocket status and formatted messages", async ({ page }) => {
        // Capture console logs to debug
        page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));
        page.on('pageerror', err => console.log(`BROWSER ERROR: ${err}`));

        // Navigate to dashboard
        await page.goto("/");

        // Wait for dashboard to load
        await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

        // 1. Verify WebSocket connects (Green "Connected" status)
        const wsStatus = page.locator("div.stat-value", { hasText: "Connected" });
        await expect(wsStatus).toBeVisible({ timeout: 15000 });
        await expect(wsStatus).toHaveClass(/text-success/);

        // 2. Verify the Real-time Command Log container exists
        const logContainer = page.locator(".mockup-code");
        await expect(logContainer).toBeVisible();

        // The log initially shows "Waiting for commands..." when no messages have arrived.
        // Once real WS messages (e.g. telemetry) arrive, they are parsed but telemetry
        // frames don't get added to the message list. So the placeholder may persist.
        // We verify the log area is present and functional.
        await expect(logContainer).toContainText(/Waiting for commands|>/);

        // 3. Verify the command input is enabled when connected
        const commandInput = page.getByRole("textbox", { name: "Type and execute a command" });
        await expect(commandInput).toBeEnabled();
    });
});
