import { test, expect } from "@playwright/test";

test.describe("MainLayout", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/dashboard/);
  });

  test("all sidebar nav links are visible", async ({ page }) => {
    await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Commands", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Command Authoring" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Configuration" })).toBeVisible();
  });

  test("clicking each nav item navigates to correct URL", async ({ page }) => {
    await page.getByRole("link", { name: "Commands", exact: true }).click();
    await expect(page).toHaveURL(/\/commands$/);

    await page.getByRole("link", { name: "Command Authoring" }).click();
    await expect(page).toHaveURL(/\/commands\/authoring/);

    await page.getByRole("link", { name: "Configuration" }).click();
    await expect(page).toHaveURL(/\/configuration/);

    await page.getByRole("link", { name: "Dashboard" }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("active nav item has visual indicator", async ({ page }) => {
    // On /dashboard, the Dashboard link should have the active class
    const dashboardLink = page.getByRole("link", { name: "Dashboard" });
    await expect(dashboardLink).toHaveClass(/active/);
    await expect(dashboardLink).toHaveClass(/border-primary/);

    // Navigate to Commands and verify it becomes active
    await page.getByRole("link", { name: "Commands", exact: true }).click();
    await expect(page).toHaveURL(/\/commands$/);

    const commandsLink = page.getByRole("link", { name: "Commands", exact: true });
    await expect(commandsLink).toHaveClass(/active/);

    // Dashboard link should no longer be active
    await expect(dashboardLink).not.toHaveClass(/active/);
  });

  test("logout button is visible and clickable", async ({ page }) => {
    const logoutButton = page.getByRole("button", { name: "Logout" });
    await expect(logoutButton).toBeVisible();
    await expect(logoutButton).toBeEnabled();
  });
});

test.describe("MainLayout - Mobile Viewport", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/dashboard/);
  });

  test("hamburger menu toggle works", async ({ page }) => {
    // Sidebar should be off-screen initially on mobile
    const sidebar = page.locator("aside");
    await expect(sidebar).toHaveClass(/-translate-x-full/);

    // Click hamburger menu to open sidebar
    await page.getByRole("button", { name: "Open sidebar" }).click();

    // Sidebar should now be visible (translate-x-0)
    await expect(sidebar).toHaveClass(/translate-x-0/);

    // Close sidebar via the close button
    await page.getByRole("button", { name: "Close sidebar" }).click();
    await expect(sidebar).toHaveClass(/-translate-x-full/);
  });

  test("clicking nav item closes sidebar", async ({ page }) => {
    const sidebar = page.locator("aside");

    // Open sidebar
    await page.getByRole("button", { name: "Open sidebar" }).click();
    await expect(sidebar).toHaveClass(/translate-x-0/);

    // Click a nav item
    await page.getByRole("link", { name: "Commands", exact: true }).click();
    await expect(page).toHaveURL(/\/commands$/);

    // Sidebar should close after navigation (useEffect on location.pathname)
    await expect(sidebar).toHaveClass(/-translate-x-full/);
  });

  test("clicking backdrop closes sidebar", async ({ page }) => {
    const sidebar = page.locator("aside");

    // Open sidebar
    await page.getByRole("button", { name: "Open sidebar" }).click();
    await expect(sidebar).toHaveClass(/translate-x-0/);

    // The backdrop is a div with fixed inset-0 and bg-black/50
    const backdrop = page.locator("div.fixed.inset-0");
    await expect(backdrop).toBeVisible();

    // Click the backdrop
    await backdrop.click({ position: { x: 350, y: 300 } });

    // Sidebar should close
    await expect(sidebar).toHaveClass(/-translate-x-full/);
  });
});
