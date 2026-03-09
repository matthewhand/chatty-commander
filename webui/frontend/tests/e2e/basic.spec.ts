import { test, expect } from "@playwright/test";

test("basic page load", async ({ page }) => {
  await page.goto("/");
  // Should redirect to dashboard (with no auth)
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.locator("h2:has-text('Dashboard')")).toBeVisible();
});

test("navigation works", async ({ page }) => {
  await page.goto("/");
  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/dashboard/);

  // Navigate to Configuration
  await page.click("text=Configuration");
  await expect(page).toHaveURL(/configuration/);

  // Navigate back to Dashboard
  await page.click("text=Dashboard");
  await expect(page).toHaveURL(/dashboard/);
});

test("navigation menu items are visible", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/dashboard/);

  // Check that main navigation items are present in the navigation
  await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Configuration' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Audio Settings' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Personas' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Agent Status' })).toBeVisible();
});