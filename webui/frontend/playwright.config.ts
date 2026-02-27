import { defineConfig, devices } from "@playwright/test";

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60 * 1000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:8100",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    // Run from repo root, set PYTHONPATH to src, and use uv run
    command: "cd ../.. && PYTHONPATH=src uv run python -m chatty_commander.cli.main --web --test-mode --port 8100 --no-auth",
    url: "http://localhost:8100/health",
    reuseExistingServer: !process.env.CI,
    timeout: 30 * 1000, // Increased timeout to allow for env setup if needed
  },
});
