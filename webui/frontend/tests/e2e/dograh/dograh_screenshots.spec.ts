import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../../docs/screenshots/dograh");

const DOGRAH_EMAIL = process.env.DOGRAH_DEMO_EMAIL || "cc-dograh@example.com";
const DOGRAH_PASSWORD =
  process.env.DOGRAH_DEMO_PASSWORD || "8B5DGqjlyDZANyPlktv+gnZiT6VgJfcn";

test.describe("Dograh integration screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  });

  test("login-page", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "01-login.png"),
      fullPage: true,
    });
  });

  test("dashboard-after-signin", async ({ page, request }) => {
    // Step 1: Log in via the backend to get a JWT.
    const apiBase =
      process.env.DOGRAH_API_BASE || "http://localhost:8020";
    const loginRes = await request.post(`${apiBase}/api/v1/auth/login`, {
      data: { email: DOGRAH_EMAIL, password: DOGRAH_PASSWORD },
    });
    expect(loginRes.ok()).toBeTruthy();
    const { token, user } = await loginRes.json();

    // Step 2: Set the dograh-ui session cookie via its server route.
    // Visit the UI origin first so the request inherits its cookies/storage.
    await page.goto("/auth/login");
    const sessionRes = await page.request.post("/api/auth/session", {
      data: { token, user },
    });
    expect(sessionRes.ok()).toBeTruthy();

    // Step 3: Navigate to the post-login landing page.
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "02-dashboard.png"),
      fullPage: true,
    });
  });
});
