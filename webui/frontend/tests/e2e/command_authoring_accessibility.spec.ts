import { test, expect } from '@playwright/test';

test.describe('Command Authoring Accessibility', () => {
  test('Form validation properties are present', async ({ page }) => {
    await page.goto('/commands/authoring');

    // Make sure we are in Manual Mode by default
    // We may need to switch tab if 'ai' is default
    const manualTab = page.locator('button', { hasText: 'Manual Editor' }).first();
    if (await manualTab.isVisible()) {
        await manualTab.click();
    }

    // Wait for the manual mode panel to actually show
    await expect(page.locator('#manual-mode-panel')).toBeVisible();

    const nameInput = page.locator('#cmd-name');

    // Focus and blur to trigger validation
    await nameInput.focus();
    await nameInput.blur();

    // Verify aria-invalid is true and aria-describedby points to the error message
    await expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    await expect(nameInput).toHaveAttribute('aria-describedby', 'cmd-name-error');

    const errorMessage = page.locator('#cmd-name-error');
    await expect(errorMessage).toBeVisible();
  });
});
