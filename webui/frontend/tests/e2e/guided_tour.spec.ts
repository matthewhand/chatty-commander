import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");

// ---------------------------------------------------------------------------
// Guided Tour Screenshots
//
// Captures the full first-run user story (login -> dashboard -> configuration
// -> command authoring -> commands list -> theming -> audio -> websocket) as
// numbered tour-XX-*.png images embedded by docs/user-guide/00_GUIDED_TOUR.md.
//
// All backend data is mocked via page.route() so the captures are stable and
// reproducible, mirroring screenshots.spec.ts.
// ---------------------------------------------------------------------------

const TOUR_HEALTH = {
  status: "healthy",
  uptime: "3d 12h 45m",
  commands_executed: 1247,
  version: "1.0.0",
  cpu_usage: "23.5",
  memory_usage: "61.2",
};

const TOUR_AGENT_STATS = {
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

// CommandsPage expects a Record<string, CommandConfig> from /api/v1/commands.
// "hello_world" is the example command authored during the tour.
const TOUR_COMMANDS = {
  take_screenshot: { action: "keypress", keys: "alt+print_screen" },
  cycle_window: { action: "keypress", keys: "alt+tab" },
  toggle_mute: { action: "keypress", keys: "ctrl+shift+m" },
  hello_world: { action: "url", url: "https://example.com/hello" },
};

const TOUR_CONFIG = {
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
  commands: TOUR_COMMANDS,
  _env_overrides: { api_key: false, base_url: false, model: false },
};

const TOUR_AUDIO_DEVICES = {
  input: ["USB Microphone", "Built-in Microphone"],
  output: ["External Speakers", "HDMI Audio", "Built-in Speakers"],
};

const TOUR_VOICE_MODELS = {
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Mocks for the dashboard: health stats, agents, and dograh integration. */
async function mockDashboardAPIs(page: Page) {
  await page.route("**/health", (route) =>
    route.fulfill({ status: 200, json: TOUR_HEALTH })
  );
  await page.route("**/api/v1/advisors/context/stats", (route) =>
    route.fulfill({ status: 200, json: TOUR_AGENT_STATS })
  );
  await page.route("**/api/v1/dograh/status", (route) =>
    route.fulfill({
      status: 200,
      json: {
        available: true,
        reason: null,
        health: { status: "ok", version: "1.30.0", deployment_mode: "oss" },
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

/** Mocks for the configuration page: config, audio devices, voice models. */
async function mockConfigurationAPIs(page: Page) {
  await page.route("**/api/v1/config", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, json: TOUR_CONFIG });
    }
    return route.fulfill({ status: 200, json: { status: "ok" } });
  });
  await page.route("**/api/v1/audio/devices", (route) =>
    route.fulfill({ status: 200, json: TOUR_AUDIO_DEVICES })
  );
  await page.route("**/api/v1/models/files", (route) =>
    route.fulfill({ status: 200, json: TOUR_VOICE_MODELS })
  );
  await page.route("**/api/v1/advisors/**", (route) =>
    route.fulfill({ status: 200, json: { contexts: {}, total: 0 } })
  );
}

/** Mocks for the commands list and authoring pages. */
async function mockCommandsAPIs(page: Page) {
  await page.route("**/api/v1/commands", (route) =>
    route.fulfill({ status: 200, json: TOUR_COMMANDS })
  );
  await page.route("**/api/v1/config", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, json: TOUR_CONFIG });
    }
    return route.fulfill({ status: 200, json: { status: "ok" } });
  });
}

function shot(name: string) {
  return path.join(SCREENSHOTS_DIR, name);
}

/** Let framer-motion entrance animations finish so captures aren't mid-fade. */
async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(900);
}

// ---------------------------------------------------------------------------
// Tour
// ---------------------------------------------------------------------------

test.describe("Guided Tour Screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  });

  // The tour is shot at a consistent 1280x800 laptop viewport.
  test.use({ viewport: { width: 1280, height: 800 } });

  test("01 login page", async ({ page }) => {
    // The test backend runs with --no-auth, which silently redirects /login to
    // the dashboard. Force the real login experience by making the no-auth
    // probe (GET /api/v1/config without a token) fail, exactly as it would on
    // a production install with auth enabled.
    await page.route("**/api/v1/config", (route) =>
      route.fulfill({ status: 401, json: { detail: "Not authenticated" } })
    );

    await page.goto("/login");

    // The auth provider retries its probe a few times before giving up, so
    // allow extra time for the login card to appear.
    await expect(
      page.getByRole("heading", { name: "Chatty Commander" })
    ).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("button", { name: /login/i })).toBeVisible();

    await page.screenshot({ path: shot("tour-01-login.png"), fullPage: true });
  });

  test("02 dashboard overview", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.goto("/");
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "Healthy" })).toBeVisible();
    // Dograh integration card should report the mocked healthy state.
    await expect(page.getByTestId("dograh-status-card")).toHaveAttribute(
      "data-dograh-state",
      "online"
    );
    await expect(page.getByText("1 workflow", { exact: true })).toBeVisible();
    await settle(page);

    await page.screenshot({ path: shot("tour-02-dashboard.png"), fullPage: true });
  });

  test("03 configuration page", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/");
    await page.getByRole("link", { name: "Configuration" }).click();

    await expect(page).toHaveURL(/configuration/);
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();
    await expect(page.getByText("hey_jarvis_v0.1.onnx")).toBeVisible();
    await settle(page);

    await page.screenshot({ path: shot("tour-03-configuration.png"), fullPage: true });
  });

  test("04 command authoring with example data", async ({ page }) => {
    await mockCommandsAPIs(page);

    await page.goto("/commands/authoring");
    await expect(page).toHaveURL(/authoring/);
    await expect(
      page.getByRole("heading", { name: /command authoring/i })
    ).toBeVisible();

    // Use the manual editor and author a simple "hello_world" command that
    // opens a URL when triggered.
    await page.getByRole("tab", { name: /manual mode/i }).click();
    await page.locator("#cmd-name").fill("hello_world");
    await page.locator("#cmd-display-name").fill("Hello World");
    await page.locator("#cmd-wakeword").fill("hello world");
    await page.getByRole("button", { name: /add action/i }).click();
    await page.locator("#action-type-0").selectOption("url");
    await page.locator("#action-url-0").fill("https://example.com/hello");

    await expect(page.getByRole("button", { name: /save command/i })).toBeEnabled();
    await settle(page);

    await page.screenshot({
      path: shot("tour-04-command-authoring.png"),
      fullPage: true,
    });
  });

  test("05 commands list with the new command", async ({ page }) => {
    await mockCommandsAPIs(page);

    await page.goto("/");
    await page.getByRole("link", { name: "Commands" }).click();

    await expect(page).toHaveURL(/commands/);
    await expect(
      page.getByRole("heading", { name: /commands & triggers/i })
    ).toBeVisible();
    // The authored hello_world command is present in the grid.
    await expect(page.getByLabel("Options for hello_world")).toBeVisible();
    await settle(page);

    await page.screenshot({ path: shot("tour-05-commands-list.png"), fullPage: true });
  });

  test("06 switching the theme", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();

    // Pick a non-default DaisyUI theme to show live theming.
    await page.locator("#config-theme").selectOption("synthwave");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "synthwave");
    await settle(page);

    await page.screenshot({
      path: shot("tour-06-theme-synthwave.png"),
      fullPage: true,
    });
  });

  test("07 audio settings", async ({ page }) => {
    await mockConfigurationAPIs(page);

    await page.goto("/configuration");
    await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();

    // Choose mocked devices so the dropdowns show a realistic selection.
    const audioHeading = page.getByText("Audio Devices").first();
    await expect(audioHeading).toBeVisible();
    await page.locator("select.select-primary").selectOption("USB Microphone");
    await page.locator("select.select-secondary").selectOption("External Speakers");
    await audioHeading.scrollIntoViewIfNeeded();
    await settle(page);

    // Viewport (not full-page) capture so the audio cards fill the frame.
    await page.screenshot({ path: shot("tour-07-audio-settings.png") });
  });

  test("08 websocket status indicator", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // The WebSocket stat connects to the live test backend (the /ws endpoint
    // is not mocked), so the indicator reflects a genuine connection.
    const wsStatus = page.locator(".stat-value", { hasText: "Connected" });
    await expect(wsStatus).toBeVisible({ timeout: 15_000 });
    await settle(page);

    // Focused capture of just the WebSocket stat card.
    const wsCard = page.locator(".stats", { has: wsStatus });
    await wsCard.screenshot({ path: shot("tour-08-websocket-status.png") });
  });
});
