import { test, expect } from '@playwright/test';

test('Verify audio settings configuration, API integration, and persistence', async ({ page }) => {
  // 1. Go to Configuration page
  // Intercept the API call to verify it happens
  const devicesResponsePromise = page.waitForResponse(response =>
    response.url().includes('/api/audio/devices') && response.status() === 200
  );

  await page.goto('/configuration');

  // Wait for the API response
  const response = await devicesResponsePromise;
  expect(response.ok()).toBeTruthy();

  // Verify response body structure
  const json = await response.json();
  expect(json).toHaveProperty('input');
  expect(json).toHaveProperty('output');
  expect(json.input.length).toBeGreaterThan(0);
  expect(json.output.length).toBeGreaterThan(0);

  // 2. Locate audio devices section
  const audioSection = page.locator('h3', { hasText: 'Audio Devices' });
  await expect(audioSection).toBeVisible();

  // 3. Set a new Input Device
  const inputSelect = page.locator('select', { hasText: 'Select device...' }).first();
  await expect(inputSelect).toBeVisible();

  // Select the first available option (which might be "Default Input" in mock mode)
  const firstInputOption = await inputSelect.locator('option').nth(1).textContent(); // nth(0) is disabled placeholder
  if (firstInputOption) {
      await inputSelect.selectOption({ label: firstInputOption });
  }

  // 4. Set a new Output Device
  const outputSelect = page.locator('select', { hasText: 'Select device...' }).nth(1);
  await expect(outputSelect).toBeVisible();

  const firstOutputOption = await outputSelect.locator('option').nth(1).textContent();
  if (firstOutputOption) {
      await outputSelect.selectOption({ label: firstOutputOption });
  }

  // 5. Save Changes
  // Intercept the PUT /api/v1/config call (which persists the main config)
  // AND potentially the POST /api/audio/device calls if the frontend makes them immediately on change or on save
  const saveButton = page.getByRole('button', { name: 'Save Changes' });
  await saveButton.click();

  // Verify success message
  await expect(page.locator('text=✓ Saved')).toBeVisible();

  // 6. Reload and Verify Persistence
  // Reload the page and check if the API returns the saved defaults
  const reloadResponsePromise = page.waitForResponse(response =>
    response.url().includes('/api/audio/devices') && response.status() === 200
  );

  await page.reload();
  const reloadResponse = await reloadResponsePromise;
  const reloadJson = await reloadResponse.json();

  // In our mock implementation, setting the device updates the config,
  // and get_audio_devices reads that config to set default_input/default_output.
  if (firstInputOption) {
      expect(reloadJson.default_input).toBe(firstInputOption);
  }
  if (firstOutputOption) {
      expect(reloadJson.default_output).toBe(firstOutputOption);
  }
});
