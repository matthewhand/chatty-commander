import { test, expect } from "@playwright/test";

test.describe("Audio Configuration", () => {
    test("should load and save audio devices correctly", async ({ page }) => {
        // No mocking: we test against the real backend now.
        // This requires the backend to be running and returning valid data (or empty lists).

        await page.goto("/configuration");

        // Wait for the UI to settle
        await page.waitForTimeout(2000);

        // Find the input device select element
        // Depending on backend state (pyaudio installed or not), we might have options or just "Select device..."
        const inputSelect = page.locator('select').filter({ hasText: 'Select device...' }).first();

        // Verify we can interact with it
        await expect(inputSelect).toBeVisible();

        // Test the POST endpoint (saving a device)
        // We'll simulate a selection if options exist, or just verify the endpoint exists by manually triggering a save via console if needed,
        // but cleaner is to just select the first available option if any.

        const optionCount = await inputSelect.locator('option').count();
        if (optionCount > 1) {
             // Select the first real option
             const firstOption = await inputSelect.locator('option').nth(1).getAttribute('value');
             if (firstOption) {
                 await inputSelect.selectOption(firstOption);

                 // Verify the save request happened (optimistic UI update in component)
                 // The component auto-saves on mutation success, but mutation is triggered on component unmount or explicit save?
                 // Looking at ConfigurationPage.tsx:
                 // const mutation = useMutation({ mutationFn: persistConfig, onSuccess: ... if (inputDevice) saveAudioSettings(...) })
                 // So we need to click "Save Changes" to trigger the POST.

                 const saveButton = page.locator('button', { hasText: 'Save Changes' });
                 await saveButton.click();

                 // Verify success message
                 await expect(page.locator('text=✓ Saved')).toBeVisible();
             }
        } else {
            // If no devices, we can at least verify the GET request succeeded (didn't crash)
            // and the UI rendered the empty state correctly.
             await expect(inputSelect).toHaveValue("");
        }
    });
});
