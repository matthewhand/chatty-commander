import { test, expect } from "@playwright/test";

test.describe("Login Page", () => {
  // The server runs with --no-auth, so the auth service falls back to the
  // config endpoint and auto-authenticates as local_admin. To render the
  // login page we must block BOTH the auth/me AND config endpoints so
  // getCurrentUser() throws and the app enters auth-required mode.
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Not authenticated" }),
      });
    });

    await page.route("**/api/v1/config", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Not authenticated" }),
      });
    });

    await page.goto("/login");
    // Wait for the auth provider to finish its retry cycle and settle.
    // The AuthProvider retries up to 5 times with increasing delays before
    // giving up, but route interception responds instantly so retries
    // resolve quickly. Wait for the login heading to appear.
    await expect(
      page.getByRole("heading", { name: "Chatty Commander" })
    ).toBeVisible({ timeout: 30_000 });
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

  // Note: testing form submission (login failure / success) is not feasible in
  // E2E with --no-auth because useAuth.login() sets context-level loading=true,
  // which causes AppContent to unmount LoginPage and show a spinner. The local
  // error state in LoginPage is lost on re-mount. Login submission behavior is
  // covered by unit tests instead.
});
