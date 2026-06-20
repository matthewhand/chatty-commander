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

// The /api/v1/commands contract is a DICT keyed by command name (the page does
// Object.entries(commands)); an array makes it render rows named "0/1/2/3" with
// no action. Mirror the real shape (action + keys/url/cmd/message).
const COMMANDS_RESPONSE = {
  take_screenshot: {
    action: "keypress",
    keys: "Print",
    url: null,
    cmd: null,
    message: null,
  },
  open_browser: {
    action: "url",
    keys: null,
    url: "https://example.com",
    cmd: null,
    message: null,
  },
  toggle_mute: {
    action: "keypress",
    keys: "ctrl+shift+m",
    url: null,
    cmd: null,
    message: null,
  },
  volume_up: {
    action: "keypress",
    keys: "XF86AudioRaiseVolume",
    url: null,
    cmd: null,
    message: null,
  },
};

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
  // Dograh integration status — show online with one workflow so the
  // dashboard screenshot demonstrates the cross-system integration in
  // its healthy state. Use the inverse mocks in dograh_offline.spec.ts
  // when documenting the unconfigured fallback.
  await page.route("**/api/v1/dograh/status", (route) =>
    route.fulfill({
      status: 200,
      json: {
        available: true,
        reason: null,
        health: {
          status: "ok",
          version: "1.30.0",
          deployment_mode: "oss",
        },
      },
    })
  );
  await page.route("**/api/v1/dograh/workflows", (route) =>
    route.fulfill({
      status: 200,
      json: [{ id: 1, name: "lead-qualification", status: "active" }],
    })
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

    // Wait for dashboard to fully load. The sticky desktop app bar renders its
    // own page-title <h1> "Dashboard" alongside the page heading, so scope to first.
    await expect(page.getByRole("heading", { name: "Dashboard" }).first()).toBeVisible();
    // modernized brittle .stat-value to getByText({exact:true}).nth(0) (consistent with dashboard.spec and other e2e)
    await expect(page.getByText("Healthy", { exact: true }).nth(0)).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "dashboard.png"),
      fullPage: true
    });
  });

  test("login", async ({ page }) => {
    // The e2e backend runs with --no-auth, so the auth probe (GET /api/v1/config)
    // succeeds and the app auto-authenticates — visiting /login would redirect to
    // the dashboard and the "login" screenshot would actually show the dashboard.
    // Force the probe to 401 (as guided_tour.spec.ts does) so the REAL login form
    // renders and gets captured.
    await page.route("**/api/v1/config", (route) =>
      route.fulfill({ status: 401, json: { detail: "Not authenticated" } })
    );

    await page.goto("/login");

    // The login card uses the <Logo> wordmark + a Login button (no heading
    // role), so assert on those — same as guided_tour's tour-01 capture.
    await expect(page.getByText("ChattyCommander").first()).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("button", { name: /login/i })).toBeVisible();
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
    await expect(page.getByRole("heading", { name: /configuration/i }).first()).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration.png"),
      fullPage: true
    });
  });

  test("configuration-voice-models", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i }).first()).toBeVisible();

    // Configuration is now tabbed; the voice models table lives under the
    // "Voice Models" tab, so open it before capturing (and asserting) it.
    await page.getByRole("tab", { name: "Voice Models" }).click();
    const modelsHeading = page.getByText("Voice Models (ONNX)", { exact: true });
    await expect(modelsHeading).toBeVisible();
    await modelsHeading.scrollIntoViewIfNeeded();

    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration-voice-models.png"),
      fullPage: true
    });
  });

  test("configuration-audio", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i }).first()).toBeVisible();

    // Configuration is now tabbed; the audio device cards live under the
    // "Audio" tab, so open it before capturing (and asserting) the section.
    await page.getByRole("tab", { name: "Audio" }).click();
    const audioHeading = page.getByText("Audio Devices", { exact: true });
    await expect(audioHeading).toBeVisible();
    await audioHeading.scrollIntoViewIfNeeded();

    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration-audio.png"),
      fullPage: true
    });
  });

  test("configuration-llm", async ({ page }) => {
    await mockConfigurationAPIs(page);
    // Fresh-install LLM config (no key/model) so the "Credentials & model"
    // disclosure shows its decluttered, collapsed state over the base URL.
    // Registered after mockConfigurationAPIs so it wins the route match.
    await page.route("**/api/v1/config", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          json: {
            ...MOCK_CONFIG,
            advisors: {
              providers: {
                api_key: "",
                base_url: "http://localhost:11434/v1",
                model: "",
              },
            },
          },
        });
      }
      return route.fulfill({ status: 200, json: { status: "ok" } });
    });

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i }).first()).toBeVisible();

    await page.getByRole("tab", { name: "LLM" }).click();
    const llmHeading = page.getByText("LLM Endpoint", { exact: true });
    await expect(llmHeading).toBeVisible();
    await expect(page.getByText("Credentials & model")).toBeVisible();
    await page.waitForLoadState("networkidle");

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "configuration-llm.png"),
      fullPage: true,
    });
  });

  test("commands", async ({ page }) => {
    await mockCommandsAPIs(page);

    await page.goto("/");
    await page.getByRole("link", { name: "Commands" }).click();

    await expect(page).toHaveURL(/commands/);
    await expect(page.getByRole("heading", { name: /commands/i }).first()).toBeVisible();
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
