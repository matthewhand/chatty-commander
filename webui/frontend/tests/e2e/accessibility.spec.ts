import { test, expect } from '@playwright/test';

test('Commands page accessibility test', async ({ page }) => {
  // Navigate to commands page
  await page.goto('/commands');

  // Wait for content (MOCK_COMMANDS are client-side so should load fast)
  // Look for a known command
  const commandCard = page.locator('.card-title', { hasText: 'Turn On Lights' });
  await expect(commandCard).toBeVisible();

  // 1. Check for Aria Labels on buttons
  // The aria-label is on the button itself
  const editBtn = page.getByRole('button', { name: 'Edit Turn On Lights' });
  await expect(editBtn).toBeVisible();

  const deleteBtn = page.getByRole('button', { name: 'Delete Turn On Lights' });
  await expect(deleteBtn).toBeVisible();

  // 2. Check for Tooltips (CSS based)
  // The button is wrapped in a div with .tooltip class and data-tip attribute
  const editTooltipWrapper = page.locator('.tooltip', { hasText: 'Edit Command' }).filter({ has: editBtn });
  await expect(editTooltipWrapper).toBeVisible();

  // Hover to trigger visual tooltip (for screenshot)
  await editTooltipWrapper.hover();

  // 3. Check Toggle Accessibility
  const toggle = page.getByRole('checkbox', { name: 'Toggle Lights On wakeword' });
  await expect(toggle).toBeVisible();

  // Take screenshot of the state
  await page.screenshot({ path: 'verification_commands_playwright.png' });
});