import { test, expect } from "@playwright/test";

test.describe("Telemetry", () => {
    test("dashboard receives real-time system metrics", async ({ page }) => {
        // Increase timeout significantly to allow for app startup, auth check, and WS connection
        test.setTimeout(45000);

        // Setup promise BEFORE navigation
        const wsPromise = page.waitForEvent("websocket", { timeout: 30000 });

        // Navigate to dashboard
        await page.goto("/");

        // Wait for URL to confirm we are logged in / authorized (even in no-auth mode)
        await expect(page).toHaveURL(/dashboard/, { timeout: 15000 });

        // Wait for WebSocket connection
        console.log("Waiting for WebSocket connection...");
        const ws = await wsPromise;
        console.log("WebSocket connected!");

        // Wait for telemetry frame
        console.log("Waiting for telemetry frame...");
        const telemetryFrame = await ws.waitForEvent("framereceived", {
            predicate: (frame) => {
                const payload = frame.payload();
                if (!payload) return false;
                try {
                    const text = payload.toString();
                    // console.log("WS RECV:", text);
                    const json = JSON.parse(text);
                    return json.type === "telemetry" && json.data;
                } catch (e) {
                    return false;
                }
            },
            timeout: 20000
        });

        expect(telemetryFrame).toBeTruthy();
    });
});
