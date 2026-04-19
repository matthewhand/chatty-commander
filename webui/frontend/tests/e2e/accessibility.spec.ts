import { test, expect } from '@playwright/test';

test('Commands page accessibility test', async ({ page }) => {
  // Navigate to commands page
  await page.goto('/commands');

  // Wait for content
  await expect(page.getByRole('heading', { name: 'Commands & Triggers' })).toBeVisible();

  // Wait until we actually fetch the commands and they render
  await expect(page.getByRole('heading', { name: 'take_screenshot' }).first()).toBeVisible();

  // 1. Check for Aria Labels on dropdown menu buttons
  // The Edit/Delete buttons are inside a DynamicDropdown (hidden until opened).
  // Click the dropdown trigger (a "..." kebab menu button) to reveal menu items.
  const dropdownTrigger = page.locator('button[aria-haspopup="true"]').first();
  await expect(dropdownTrigger).toBeVisible();
  await dropdownTrigger.click();

  const editBtn = page.getByRole('button', { name: 'Edit take_screenshot' });
  await expect(editBtn).toBeVisible();

  const deleteBtn = page.getByRole('button', { name: 'Delete take_screenshot' });
  await expect(deleteBtn).toBeVisible();

  // Close the dropdown by clicking elsewhere
  await page.locator('body').click({ position: { x: 0, y: 0 } });

  // 2. Check that the REST API section is present, which is common to all commands.
  await expect(page.getByText('REST API Trigger').first()).toBeVisible();

  // Take screenshot of the state
  await page.screenshot({ path: 'verification_commands_playwright.png' });
});
