import { test, expect } from "@playwright/test";

test.describe("Audio Settings", () => {
    test("fetch audio devices endpoint exists", async ({ page }) => {
        // Go to configuration page
        await page.goto("/configuration");

        // Wait for the specific request to /api/audio/devices
        // We expect this to SUCCEED now (200)
        const response = await page.waitForResponse(
            (resp) => resp.url().includes("/api/audio/devices") && resp.status() === 200,
            { timeout: 5000 }
        );

        // Assert that we got the 200 response
        expect(response.status()).toBe(200);

        // Also verify the response body structure if possible
        const body = await response.json();
        expect(body).toHaveProperty("input");
        expect(body).toHaveProperty("output");
        expect(Array.isArray(body.input)).toBe(true);
        expect(Array.isArray(body.output)).toBe(true);
    });
});
