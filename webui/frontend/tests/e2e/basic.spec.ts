import { test, expect } from "@playwright/test";

test("basic page load", async ({ page }) => {
  await page.goto("/");
  // Should redirect to dashboard (with no auth)
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("navigation works", async ({ page }) => {
  await page.goto("/");
  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/dashboard/);

  // Navigate to Configuration
  await page.getByRole('link', { name: 'Configuration' }).click();
  await expect(page).toHaveURL(/configuration/);
  await page.waitForLoadState('domcontentloaded'); // small addition for nav stability
  // expand journey: check configuration heading visible (modern getByRole DOM check)
  await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();

  // Navigate back to Dashboard
  await page.getByRole('link', { name: 'Dashboard' }).click();
  await expect(page).toHaveURL(/dashboard/);
});

test("navigation menu items are visible", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/dashboard/);

  // Check that main navigation items are present in the navigation
  // (must match the navItems in src/components/MainLayout.tsx)
  await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Configuration' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Commands', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Voice Test' })).toBeVisible();
});