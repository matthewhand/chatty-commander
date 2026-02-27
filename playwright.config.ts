import { defineConfig, devices } from "@playwright/test";

/**
 * Read environment variables from file.
 * https://playwright.dev/docs/test-configuration#environment-variables
 */
function getEnvVar(name: string): string | undefined {
  const env = process.env;
  return env[name];
}

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
    // We are mocking the backend, but we need the frontend to be served
    // For e2e, we usually test against the real backend, but for this reproduction
    // we want to verify the frontend's handling of API data.
    // However, the current webServer config tries to start the backend.
    // Since we are having trouble starting the backend in this environment (ModuleNotFoundError),
    // and we only need the frontend for this test (mocking the API),
    // we will start the frontend dev server instead.
    baseURL: "http://localhost:3000", // Vite default port configured in vite.config.ts
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    // Start the frontend dev server
    command: "cd webui/frontend && pnpm dev",
    // Wait for the frontend to be ready
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
