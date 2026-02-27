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
    // For this mock test, we can just run against the dev server
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    // Just start the frontend dev server, don't try to start the backend
    command: "pnpm dev",
    port: 3000,
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
