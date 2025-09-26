import { test, expect } from "@playwright/test";

test("basic page load", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Chatty Commander/);
  await expect(page.locator("h1")).toContainText("Dashboard");
});

test("navigation works", async ({ page }) => {
  await page.goto("/");
  await page.click("text=Config");
  await expect(page).toHaveURL(/config/);
});
