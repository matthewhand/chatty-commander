import { test, expect } from '@playwright/test';

test('WebSocket connection succeeds with dynamic port', async ({ page }) => {
  // Navigate to the dashboard
  await page.goto('/');

  // Wait for the Dashboard to load
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  // Verify that the WebSocket status indicator shows "Connected"
  // This confirms that the frontend is successfully connecting to the backend on the correct port (8100)
  await expect(page.locator('.stat-value', { hasText: 'Connected' })).toBeVisible();
});
