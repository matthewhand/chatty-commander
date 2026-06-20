import { test, expect } from '@playwright/test';

test('WebSocket connection succeeds with dynamic port', async ({ page }) => {
  // Navigate to the dashboard
  await page.goto('/');

  // Wait for the Dashboard to load
  await expect(page.getByRole("heading", { name: "Dashboard" }).first()).toBeVisible();

  // Verify that the WebSocket status indicator shows "Connected"
  // This confirms that the frontend is successfully connecting to the backend on the correct port (8100)
  // modernized to getByText({exact:true}).nth(0) (no legacy .stat-value)
  await expect(page.getByText('Connected', { exact: true }).nth(0)).toBeVisible();

  // +1 wired endpoint assert (health via fetch)
  const healthOk = await page.evaluate(async () => (await fetch('/health')).ok);
  expect(healthOk).toBeTruthy();

  // +1 wired /api/v1/status (uncovered in this spec; expands per WEBUI_ISSUES working + ROADMAP e2e)
  const statusOk = await page.evaluate(async () => (await fetch('/api/v1/status')).ok);
  expect(statusOk).toBeTruthy();
});
