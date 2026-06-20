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
    // The overhauled sidebar marks the active link with aria-current="page"
    // (plus a self-contained highlight: bg-primary + left bar). The old
    // `.active`/`.border-primary` DaisyUI classes are gone, so assert on the
    // accessible state instead, which is the stable contract for active nav.
    const dashboardLink = page.getByRole("link", { name: "Dashboard" });
    await expect(dashboardLink).toHaveAttribute("aria-current", "page");
    await expect(dashboardLink).toHaveClass(/bg-primary/);

    // Navigate to Commands and verify it becomes active
    await page.getByRole("link", { name: "Commands", exact: true }).click();
    await expect(page).toHaveURL(/\/commands$/);

    const commandsLink = page.getByRole("link", { name: "Commands", exact: true });
    await expect(commandsLink).toHaveAttribute("aria-current", "page");

    // Dashboard link should no longer be active
    await expect(dashboardLink).not.toHaveAttribute("aria-current", "page");
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
    const sidebar = page.locator("aside").nth(0);  // modern: .nth(0) scoped instead of generic locator (avoids brittle)
    await expect(sidebar).toHaveClass(/-translate-x-full/);

    // Click hamburger menu to open sidebar
    await page.getByRole("button", { name: "Open sidebar" }).click();

    // Sidebar should now be visible (translate-x-0)
    await expect(sidebar).toHaveClass(/translate-x-0/);

    // Close sidebar via the in-sidebar close button. A backdrop overlay also
    // carries the "Close sidebar" label, so scope to the button inside the aside.
    await sidebar.getByRole("button", { name: "Close sidebar" }).click();
    await expect(sidebar).toHaveClass(/-translate-x-full/);
  });

  test("clicking nav item closes sidebar", async ({ page }) => {
    const sidebar = page.locator("aside").nth(0); // modern: .nth(0) to scope (consistent with hamburger test)

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
    const sidebar = page.locator("aside").nth(0); // modern: .nth(0) to scope (consistent with hamburger test)

    // Open sidebar
    await page.getByRole("button", { name: "Open sidebar" }).click();
    await expect(sidebar).toHaveClass(/translate-x-0/);

    // The backdrop is now a <button> (fixed inset-0, bg-black/50) so it is
    // keyboard-operable; it shares the "Close sidebar" label with the header
    // close button, so scope to the full-screen overlay by its classes.
    const backdrop = page.locator("button.fixed.inset-0");
    await expect(backdrop).toBeVisible();

    // The backdrop spans the full viewport, but the open sidebar (z-30) sits on
    // top of its left edge, so a default center click is intercepted by the
    // sidebar. Click near the right edge — the area a user taps to dismiss —
    // which is backdrop, not sidebar.
    const box = await backdrop.boundingBox();
    await backdrop.click({
      position: { x: (box?.width ?? 320) - 10, y: (box?.height ?? 400) / 2 },
    });

    // Sidebar should close
    await expect(sidebar).toHaveClass(/-translate-x-full/);
  });
});
