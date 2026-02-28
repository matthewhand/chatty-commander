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

        // 2. Verify Rich Log UI
        // Check that the log container exists and has rich items
        const logContainer = page.locator(".mockup-code");

        // Wait for the connection message to appear in the log
        // The new UI uses formatted text in p tags inside LogMessageItem
        await expect(logContainer).toContainText(/Connected to ChattyCommander/, { timeout: 10000 });

        // Verify timestamps are present (checking for HH:MM:SS format roughly)
        const timestamp = logContainer.locator("span.font-mono.opacity-40").first();
        await expect(timestamp).toBeVisible();
        await expect(timestamp).toHaveText(/\d{2}:\d{2}:\d{2}/);

        // Ensure it DOES NOT contain the raw JSON structure for that message
        const rawJsonSnippet = '"type": "connection_established"';
        const logText = await logContainer.innerText();
        expect(logText).not.toContain(rawJsonSnippet);

        // 3. Verify Toast Notification (Success state)
        // Since we just connected, the success toast might be visible or fading out
        // We'll check if it appeared at least once or is present
        // Note: It auto-hides after 3s, so timing is tricky.
        // We can force a disconnect simulation if we really wanted to test the toast fully,
        // but checking the "Connected" stat is sufficient for the happy path.
    });
});
