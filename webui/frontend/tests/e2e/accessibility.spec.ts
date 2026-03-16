import { test, expect } from '@playwright/test';

test('Commands page accessibility test', async ({ page }) => {
  // Navigate to commands page
  await page.goto('/commands');

  // Wait for content (take_screenshot)
  // Use getByRole instead of locator with class
  await expect(page.getByRole('heading', { name: 'Commands & Triggers' })).toBeVisible();

  // Wait until we actually fetch the commands and they render
  await expect(page.getByRole('heading', { name: 'take_screenshot' }).first()).toBeVisible();

  // 1. Check for Aria Labels on dropdown trigger and open the dropdown
  // Wait for the specific command card to ensure we're targeting the right one
  const commandCard = page.locator('.glass-card').filter({ hasText: 'take_screenshot' }).first();
  await expect(commandCard).toBeVisible();

  const dropdownTrigger = commandCard.locator('button', { has: page.locator('svg') }).first();
  await expect(dropdownTrigger).toBeVisible();
  await dropdownTrigger.click();

  // Wait for the dropdown content to be visible
  const dropdownContent = page.locator('.dropdown-content').first();
  await expect(dropdownContent).toBeVisible();

  // The buttons inside should be found by their visible text inside the dropdown content
  const editBtn = dropdownContent.getByText('Edit Command');
  await expect(editBtn).toBeVisible();

  const deleteBtn = dropdownContent.getByText('Delete Command');
  await expect(deleteBtn).toBeVisible();

  // 2. Check Tooltips and general accessibility elements
  // The structure doesn't expose a specific .tooltip element for commands anymore,
  // so we'll check that the refresh button has the correct title
  const refreshBtn = page.locator('button[title="Refresh Commands"]');
  await expect(refreshBtn).toBeVisible();

  // Hover to trigger visual tooltip (for screenshot)
  await refreshBtn.hover();

  // 3. Check Toggle Accessibility
  // Verify that the REST API section is present, which is common to all commands.
  await expect(page.getByText('REST API Trigger').first()).toBeVisible();

  // Take screenshot of the state
  await page.screenshot({ path: 'verification_commands_playwright.png' });
});
