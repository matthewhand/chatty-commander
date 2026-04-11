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
        const wsStatus = page.locator(".stat-value", { hasText: "Connected" });
        await expect(wsStatus).toBeVisible({ timeout: 15000 });
        await expect(wsStatus).toHaveClass(/text-success/);

        // 2. Verify the Real-time Command Log container exists
        // The dashboard now uses chat-style bubbles instead of mockup-code.
        // The log area is inside a card with "Real-time Command Log" heading.
        const logCard = page.locator(".card", { has: page.getByText("Real-time Command Log") });
        await expect(logCard).toBeVisible();

        // The log initially shows "Waiting for commands..." when no messages have arrived.
        const logArea = logCard.locator(".bg-base-300");
        await expect(logArea).toContainText(/Waiting for commands/);

        // 3. Verify the command input is enabled when connected
        const commandInput = page.getByLabel("Type and execute a command");
        await expect(commandInput).toBeEnabled();
    });
});
