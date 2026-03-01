import { test, expect } from "@playwright/test";

test.describe("Reproduction of Issues", () => {
  test("Commands Page shows Real Data", async ({ page }) => {
    // Navigate to the Commands page
    await page.goto("/commands");

    // Check that "Turn On Lights" (mock data) is NOT present
    const mockCommand = page.locator("text=Turn On Lights");
    await expect(mockCommand).not.toBeVisible();

    // Check for "hello" (default config command) or "take_screenshot"
    // Note: The backend default config usually has "hello" or "take_screenshot"
    const realCommand = page.locator("text=take_screenshot").or(page.locator("text=hello"));
    // We expect at least one real command to be visible eventually
    await expect(realCommand.first()).toBeVisible({ timeout: 10000 });
  });

  test("Dashboard Command Execution uses Correct URL", async ({ page }) => {
    await page.goto("/dashboard");

    // Intercept the network request for command execution
    const requestPromise = page.waitForRequest(request =>
      request.url().includes("/api/v1/command") && request.method() === "POST"
    );

    // Type and execute a command
    await page.fill('input[placeholder="Type a command to execute..."]', "hello");
    await page.click('button:has-text("Execute")');

    // Wait for the request and verify the URL
    const request = await requestPromise;
    expect(request.url()).toContain("/api/v1/command");
  });
});
