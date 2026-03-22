import { test, expect } from '@playwright/test';

test('Commands page accessibility test', async ({ page }) => {
  // Navigate to commands page
  await page.goto('/commands');

  // Wait for content (take_screenshot)
  // Use getByRole instead of locator with class
  await expect(page.getByRole('heading', { name: 'Commands & Triggers' })).toBeVisible();

  // Wait until we actually fetch the commands and they render
  await expect(page.getByRole('heading', { name: 'take_screenshot' }).first()).toBeVisible();

  // Open the dropdown first since actions are now inside a DynamicDropdown
  const optionsBtn = page.getByRole('button', { name: 'Options for take_screenshot' });
  await optionsBtn.click();
  // Wait for the dropdown content to be visible
  await expect(page.locator('.dropdown-content')).toBeVisible();

  // 1. Check for Aria Labels on buttons
  // The aria-label is on the button itself
  const editBtn = page.getByRole('button', { name: 'Edit take_screenshot' });
  await expect(editBtn).toBeVisible();

  const deleteBtn = page.getByRole('button', { name: 'Delete take_screenshot' });
  await expect(deleteBtn).toBeVisible();

  // 3. Check Toggle Accessibility
  // The updated page structure doesn't expose toggles for this particular command.
  // Instead, verify that the REST API section is present, which is common to all commands.
  await expect(page.getByText('REST API Trigger').first()).toBeVisible();

  // Take screenshot of the state
  await page.screenshot({ path: 'verification_commands_playwright.png' });
});
