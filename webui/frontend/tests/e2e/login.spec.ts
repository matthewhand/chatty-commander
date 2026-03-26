import { test, expect } from "@playwright/test";

test.describe("Login Page", () => {
  // The server runs with --no-auth, so navigating to /login will redirect
  // to /dashboard. We intercept the auth check to simulate auth-required mode
  // so the login page actually renders.
  test.beforeEach(async ({ page }) => {
    // Mock the auth endpoint to return 401, forcing the app into login mode
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Not authenticated" }),
      });
    });

    await page.goto("/login");
  });

  test("renders with title and form inputs", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Chatty Commander" })
    ).toBeVisible();

    await expect(
      page.getByPlaceholder("Enter username")
    ).toBeVisible();

    await expect(
      page.getByPlaceholder("Enter password")
    ).toBeVisible();
  });

  test("username and password inputs accept text", async ({ page }) => {
    const usernameInput = page.getByPlaceholder("Enter username");
    const passwordInput = page.getByPlaceholder("Enter password");

    await usernameInput.fill("testuser");
    await expect(usernameInput).toHaveValue("testuser");

    await passwordInput.fill("secretpass");
    await expect(passwordInput).toHaveValue("secretpass");
  });

  test("info alert about auth config is visible", async ({ page }) => {
    await expect(
      page.getByText("Auth configured via CLI. No reset function.")
    ).toBeVisible();

    await expect(
      page.getByText("Use --no-auth to disable.")
    ).toBeVisible();
  });

  test("login button exists and shows correct text", async ({ page }) => {
    const loginButton = page.getByRole("button", { name: "Login" });
    await expect(loginButton).toBeVisible();
    await expect(loginButton).toHaveText("Login");
  });

  test("form has required attribute on inputs", async ({ page }) => {
    const usernameInput = page.getByPlaceholder("Enter username");
    const passwordInput = page.getByPlaceholder("Enter password");

    await expect(usernameInput).toHaveAttribute("required", "");
    await expect(passwordInput).toHaveAttribute("required", "");
  });
});
