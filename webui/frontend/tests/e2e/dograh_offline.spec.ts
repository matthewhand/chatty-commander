import { test, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");

async function mockOfflineDashboardAPIs(page: Page) {
  await page.route("**/health", (route) =>
    route.fulfill({
      status: 200,
      json: {
        status: "healthy",
        uptime: "3d 12h 45m",
        commands_executed: 1247,
        version: "1.0.0",
        cpu_usage: "23.5",
        memory_usage: "61.2",
      },
    })
  );
  await page.route("**/api/v1/advisors/context/stats", (route) =>
    route.fulfill({ status: 200, json: { contexts: {}, total: 0 } })
  );
  await page.route("**/api/v1/commands", (route) =>
    route.fulfill({ status: 200, json: [] })
  );
  // The unavailable shape exercised here mirrors what
  // src/chatty_commander/web/routes/dograh.py returns when
  // DOGRAH_BASE_URL or DOGRAH_API_KEY is unset.
  await page.route("**/api/v1/dograh/status", (route) =>
    route.fulfill({
      status: 200,
      json: {
        available: false,
        reason: "DOGRAH_BASE_URL not configured",
        health: null,
      },
    })
  );
  await page.route("**/api/v1/dograh/workflows", (route) =>
    route.fulfill({ status: 200, json: [] })
  );
}

test.describe("Dograh degraded UI", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  });

  test.use({ viewport: { width: 1280, height: 900 } });

  test("dashboard-dograh-offline", async ({ page }) => {
    await mockOfflineDashboardAPIs(page);
    await page.goto("/");
    await page.waitForSelector('[data-testid="dograh-status-card"][data-dograh-state="unavailable"]');
    await page.waitForLoadState("networkidle");
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "dashboard-dograh-offline.png"),
      fullPage: true,
    });
  });
});
