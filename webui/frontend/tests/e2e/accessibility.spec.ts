import { test, expect } from '@playwright/test';

test('Commands page accessibility test', async ({ page }) => {
  // Navigate to commands page
  await page.goto('/commands');

  // Wait for content
  await expect(page.getByRole('heading', { name: 'Commands & Triggers' })).toBeVisible();

  // Wait until we actually fetch the commands and they render. Commands now
  // render as table rows (Wave-2 refactor), so the name is a table cell.
  await expect(page.getByRole('cell', { name: 'take_screenshot', exact: true })).toBeVisible();

  // 1. Check for Aria Labels on the per-row action controls. Edit is a link
  // (navigates to the authoring page) and Delete is a button — both have
  // accessible names and are direct row controls (no longer behind a dropdown).
  const editBtn = page.getByRole('link', { name: 'Edit take_screenshot' });
  await expect(editBtn).toBeVisible();

  const deleteBtn = page.getByRole('button', { name: 'Delete take_screenshot' });
  await expect(deleteBtn).toBeVisible();

  // The per-row "More options" dropdown trigger is also accessibly labelled.
  const dropdownTrigger = page.getByRole('button', { name: 'More options for take_screenshot' });
  await expect(dropdownTrigger).toBeVisible();

  // 2. Check that the REST API guidance is present (now a single page-level note
  // rather than a per-row block).
  await expect(page.getByText('Every command can be triggered via the REST API:')).toBeVisible();

  // Take screenshot of the state
  await page.screenshot({ path: 'verification_commands_playwright.png' });
});
