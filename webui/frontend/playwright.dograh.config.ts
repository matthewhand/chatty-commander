import { defineConfig, devices } from "@playwright/test";

/**
 * Standalone Playwright config for chatty-commander ↔ dograh integration
 * screenshots. Does NOT start CC's web server — only requires the dograh
 * docker stack (docker compose -f docker-compose.dograh.yml up -d) to be
 * running. CC integration touchpoints that need CC's API will mock or
 * spawn CC explicitly.
 */
export default defineConfig({
  testDir: "./tests/e2e/dograh",
  timeout: 60 * 1000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { outputFolder: "playwright-report-dograh", open: "never" }]],
  use: {
    baseURL: process.env.DOGRAH_UI_URL || "http://localhost:3020",
    trace: "on-first-retry",
    viewport: { width: 1280, height: 900 },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
