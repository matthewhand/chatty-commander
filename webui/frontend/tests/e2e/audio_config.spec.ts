import { test, expect } from "@playwright/test";

test.describe("Audio Configuration", () => {
    test("should fetch audio devices on load", async ({ page }) => {
        const requestPromise = page.waitForRequest(req => req.url().includes("/api/v1/audio/devices"));

        await page.goto("/configuration");

        const request = await requestPromise;
        const response = await request.response();
        expect(response?.status()).toBe(200);

        // Wait for Audio Devices section to be visible
        // This makes sure we are looking at the right part of the page
        const audioDevicesSection = page.locator('.card', { has: page.locator('h3', { hasText: 'Audio Devices' }) });
        await expect(audioDevicesSection).toBeVisible();

        // Find the specific card for Input Device within that section
        const inputDeviceCard = audioDevicesSection.locator('.card', { has: page.locator('h4', { hasText: 'Input Device' }) });
        const inputSelectLocator = inputDeviceCard.locator('select');

        await expect(inputSelectLocator).toBeVisible();

        // Wait for mock devices to populate
        await expect(inputSelectLocator).toContainText("Mock Microphone 1");

        const options = await inputSelectLocator.locator('option').allInnerTexts();

        expect(options).toContain("Select device...");
        expect(options).toContain("Mock Microphone 1");

        await inputSelectLocator.selectOption({ label: "Mock Microphone 1" });

        const saveRequestPromise = page.waitForRequest(req => req.url().includes("/api/v1/audio/device") && req.method() === 'POST');
        await page.click("text=Save Changes");

        const saveRequest = await saveRequestPromise;
        expect(saveRequest.postDataJSON()).toEqual({ device_id: "Mock Microphone 1" });

        const saveResponse = await saveRequest.response();
        expect(saveResponse?.status()).toBe(200);
    });
});
