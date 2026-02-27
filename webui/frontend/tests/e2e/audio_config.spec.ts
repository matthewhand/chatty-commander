import { test, expect } from '@playwright/test';

test('Verify audio settings configuration and API integration', async ({ page }) => {
  // 1. Go to Configuration page
  // Intercept the API call to verify it happens
  const devicesResponsePromise = page.waitForResponse(response =>
    response.url().includes('/api/audio/devices') && response.status() === 200
  );

  await page.goto('/configuration');

  // Wait for the API response
  const response = await devicesResponsePromise;
  expect(response.ok()).toBeTruthy();

  // Verify response body structure if possible
  const json = await response.json();
  expect(json).toHaveProperty('input');
  expect(json).toHaveProperty('output');

  // 2. Locate audio devices section
  const audioSection = page.locator('h3', { hasText: 'Audio Devices' });
  await expect(audioSection).toBeVisible();

  // 3. Check for input device dropdown
  const inputSelect = page.locator('select', { hasText: 'Select device...' }).first();
  await expect(inputSelect).toBeVisible();

  // 4. Verify test button functionality
  const testMicButton = page.getByRole('button', { name: 'Test' }).first();
  await expect(testMicButton).toBeDisabled(); // Disabled when no device selected

  // 5. Check output device section
  const outputSelect = page.locator('select', { hasText: 'Select device...' }).nth(1);
  await expect(outputSelect).toBeVisible();
});
