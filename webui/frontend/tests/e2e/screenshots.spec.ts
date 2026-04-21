import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");

// ---------------------------------------------------------------------------
// Mock Data (shared across screenshot tests for consistent documentation)
// ---------------------------------------------------------------------------

const HEALTH_RESPONSE = {
  status: "healthy",
  uptime: "3d 12h 45m",
  commands_executed: 1247,
  version: "1.0.0",
  cpu_usage: "23.5",
  memory_usage: "61.2",
};

const AGENT_STATS_RESPONSE = {
  contexts: {
    "discord-advisor": {
      persona_id: "helperbot",
      platform: "discord",
      last_updated: "2026-03-26T10:00:00Z",
      context_key: "discord-ctx-1",
    },
    "twitch-advisor": {
      persona_id: "streambot",
      platform: "twitch",
      last_updated: "2026-03-26T09:30:00Z",
      context_key: "twitch-ctx-1",
    },
  },
  total: 2,
};

const COMMANDS_RESPONSE = [
  { name: "take_screenshot", description: "Captures screen content" },
  { name: "cycle_window", description: "Cycles through active windows" },
  { name: "toggle_mute", description: "Toggle microphone mute state" },
  { name: "volume_up", description: "Increase system volume" },
];

const MOCK_CONFIG = {
  advisors: {
    providers: {
      api_key: "",
      base_url: "http://localhost:11434/v1",
      model: "llama3",
    },
  },
  voice: { enabled: true },
  ui: { theme: "dark" },
  services: { voiceCommands: true, restApi: true },
  _env_overrides: { api_key: false, base_url: false, model: false },
};

const MOCK_AUDIO_DEVICES = {
  input: ["USB Microphone", "Built-in Microphone"],
  output: ["External Speakers", "HDMI Audio", "Built-in Speakers"],
};

const MOCK_VOICE_MODELS = {
  models: [
    {
      name: "hey_jarvis_v0.1.onnx",
      path: "/models/hey_jarvis_v0.1.onnx",
      size_bytes: 1482752,
      size_human: "1.4 MB",
      modified: "2026-01-15T10:30:00Z",
      state: "idle",
    },
    {
      name: "ok_computer_v2.onnx",
      path: "/models/ok_computer_v2.onnx",
      size_bytes: 2097152,
      size_human: "2.0 MB",
      modified: "2026-02-20T14:00:00Z",
      state: "computer",
    },
  ],
  total_count: 2,
  total_size_bytes: 3579904,
  total_size_human: "3.4 MB",
};

const MOCK_LLM_MODELS = {
  data: [
    { id: "gpt-4o-mini" },
    { id: "llama-3.1-8b-instant" },
    { id: "mixtral-8x7b" },
  ],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Set up all API route mocks for dashboard screenshots. */
async function mockDashboardAPIs(page: Page) {
  await page.route("**/health", (route) =>
    route.fulfill({ status: 200, json: HEALTH_RESPONSE })
  );
  await page.route("**/api/v1/advisors/context/stats", (route) =>
    route.fulfill({ status: 200, json: AGENT_STATS_RESPONSE })
  );
  await page.route("**/api/v1/commands", (route) =>
    route.fulfill({ status: 200, json: COMMANDS_RESPONSE })
  );
}

/** Set up all API route mocks for configuration screenshots. */
async function mockConfigurationAPIs(page: Page) {
  await page.route("**/api/v1/config", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, json: MOCK_CONFIG });
    }
    return route.fulfill({ status: 200, json: { status: "ok" } });
  });
  await page.route("**/api/v1/audio/devices", (route) =>
    route.fulfill({ status: 200, json: MOCK_AUDIO_DEVICES })
  );
  await page.route("**/api/v1/models/files", (route) =>
    route.fulfill({ status: 200, json: MOCK_VOICE_MODELS })
  );
  await page.route("**/v1/models", (route) =>
    route.fulfill({ status: 200, json: MOCK_LLM_MODELS })
  );
  await page.route("**/api/v1/advisors/**", (route) =>
    route.fulfill({ status: 200, json: { contexts: {}, total: 0 } })
  );
}

/** Set up mocks for commands page. */
async function mockCommandsAPIs(page: Page) {
  await page.route("**/api/v1/commands", (route) =>
    route.fulfill({ status: 200, json: COMMANDS_RESPONSE })
  );
  await page.route("**/api/v1/config", (route) =>
    route.fulfill({ status: 200, json: MOCK_CONFIG })
  );
}

// ---------------------------------------------------------------------------
// Test Setup
// ---------------------------------------------------------------------------

test.describe("Documentation Screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  });

  // Use consistent viewport for all screenshots
  test.use({ viewport: { width: 1280, height: 900 } });

  test("dashboard", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.goto("/");
    // Redirects to dashboard with --no-auth
    await expect(page).toHaveURL(/dashboard/);

    // Wait for dashboard to fully load
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "Healthy" })).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "dashboard.png"),
      fullPage: true
    });
  });

  test("login", async ({ page }) => {
    // Block auth checks to force the login page to render
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

    const loginHeading = page.getByRole("heading", { name: /login|chatty commander/i });
    await expect(loginHeading.first()).toBeVisible({ timeout: 30000 });
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "login.png"),
      fullPage: true
    });
  });

  test("configuration", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/");
    await page.getByRole("link", { name: "Configuration" }).click();

    await expect(page).toHaveURL(/configuration/);
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration.png"),
      fullPage: true
    });
  });

  test("configuration-voice-models", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();

    // Scroll to voice models section if present
    const modelsHeading = page.locator("text=Voice Models (ONNX)").first();
    if (await modelsHeading.isVisible()) {
      await modelsHeading.scrollIntoViewIfNeeded();
    }

    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration-voice-models.png"),
      fullPage: true
    });
  });

  test("configuration-audio", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();

    // Scroll to audio device section
    const audioHeading = page.locator("text=Audio Devices").first();
    if (await audioHeading.isVisible()) {
      await audioHeading.scrollIntoViewIfNeeded();
    }

    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration-audio.png"),
      fullPage: true
    });
  });

  test("commands", async ({ page }) => {
    await mockCommandsAPIs(page);

    await page.goto("/");
    await page.getByRole("link", { name: "Commands" }).click();

    await expect(page).toHaveURL(/commands/);
    await expect(page.getByRole("heading", { name: /commands/i })).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "commands.png"),
      fullPage: true
    });
  });

  test("command-authoring", async ({ page }) => {
    await mockCommandsAPIs(page);

    // Mock command generation endpoint
    await page.route("**/api/v1/commands/generate", (route) =>
      route.fulfill({
        status: 200,
        json: {
          name: "toggle_mute",
          display_name: "Toggle Mute",
          description: "Toggle microphone mute state",
          actions: [{ type: "keypress", keys: "ctrl+shift+m" }],
        },
      })
    );

    await page.goto("/commands/authoring");

    await expect(page).toHaveURL(/authoring/);
    await expect(page.getByRole("heading", { name: /command authoring|author command/i })).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "command-authoring.png"),
      fullPage: true
    });
  });
});
