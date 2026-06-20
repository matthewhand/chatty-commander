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
    baseURL: "http://localhost:8100",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Make getUserMedia deterministic so audio/mic-test specs don't flake
        // under parallel worker contention: a synthetic media stream, the
        // permission prompt auto-accepted, and the mic permission pre-granted.
        permissions: ["microphone"],
        launchOptions: {
          args: [
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
            "--autoplay-policy=no-user-gesture-required",
          ],
        },
      },
    },
  ],

  webServer: {
    // CHATTY_DISABLE_RATE_LIMIT: parallel Playwright workers share one source
    // IP and would otherwise trip the 600/min limiter; the harness must not be
    // throttled (prod default stays intact).
    command: "cd ../.. && CHATTY_DISABLE_RATE_LIMIT=1 PYTHONPATH=src uv run python -m chatty_commander.cli.main --web --test-mode --port 8100 --no-auth",
    url: "http://localhost:8100/health",
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
