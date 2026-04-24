import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../../../docs/screenshots");
const JOURNEYS_DIR = path.resolve(SCREENSHOTS_DIR, "journeys");

// ---------------------------------------------------------------------------
// Mock Data (shared across screenshot tests for consistent documentation)
// ---------------------------------------------------------------------------

const HEALTH_RESPONSE = {
  status: "healthy",
  uptime: "3d 12h 45m",
  commands_executed: 1247,
  version: "0.2.0",
  cpu_usage: "23.5",
  memory_usage: "61.2",
};

const AGENT_STATS_RESPONSE = {
  contexts: {
    "discord-advisor": {
      persona_id: "helperbot",
      platform: "discord",
      last_updated: "2025-04-15T10:00:00Z",
      context_key: "discord-ctx-1",
    },
    "twitch-advisor": {
      persona_id: "streambot",
      platform: "twitch",
      last_updated: "2025-04-15T09:30:00Z",
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
      modified: "2025-01-15T10:30:00Z",
      state: "idle",
    },
    {
      name: "ok_computer_v2.onnx",
      path: "/models/ok_computer_v2.onnx",
      size_bytes: 2097152,
      size_human: "2.0 MB",
      modified: "2025-02-20T14:00:00Z",
      state: "loaded",
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

const MOCK_VOICE_COMMAND_RESPONSE = {
  success: true,
  command: "open_notepad",
  transcript: "Open Notepad",
  executed_at: "2025-04-15T10:15:00Z",
  execution_time_ms: 245,
};

const MOCK_REALTIME_STATUS = {
  is_listening: true,
  current_input: "Hey Jarvis",
  confidence: 0.97,
  timestamp: "2025-04-15T10:16:00Z",
};

const MOCK_ERROR_RESPONSE = {
  error: "Voice service unavailable",
  code: "VOICE_503",
  details: "Connection to audio backend timed out",
  timestamp: "2025-04-15T10:20:00Z",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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

async function mockCommandsAPIs(page: Page) {
  await page.route("**/api/v1/commands", (route) =>
    route.fulfill({ status: 200, json: COMMANDS_RESPONSE })
  );
  await page.route("**/api/v1/config", (route) =>
    route.fulfill({ status: 200, json: MOCK_CONFIG })
  );
}

async function mockVoiceCommandAPIs(page: Page) {
  await page.route("**/api/v1/voice/command", (route) =>
    route.fulfill({ status: 200, json: MOCK_VOICE_COMMAND_RESPONSE })
  );
  await page.route("**/api/v1/voice/status", (route) =>
    route.fulfill({ status: 200, json: MOCK_REALTIME_STATUS })
  );
}

async function mockErrorAPIs(page: Page) {
  await page.route("**/api/v1/voice/command", (route) =>
    route.fulfill({ status: 503, json: MOCK_ERROR_RESPONSE })
  );
  await page.route("**/api/v1/voice/status", (route) =>
    route.fulfill({ status: 503, json: MOCK_ERROR_RESPONSE })
  );
}

async function takeJourneyScreenshot(page: Page, journey: string, step: number) {
  await page.waitForLoadState('networkidle');
  await page.screenshot({
    path: path.join(JOURNEYS_DIR, `journey-${journey}-step-${step}.png`),
    fullPage: true
  });
}

// ---------------------------------------------------------------------------
// Test Setup
// ---------------------------------------------------------------------------

test.describe("Documentation Screenshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
    fs.mkdirSync(JOURNEYS_DIR, { recursive: true });
  });

  test.use({ viewport: { width: 1280, height: 900 } });

  // =========================================================================
  // EXISTING BASIC SCREENSHOTS (Maintain backward compatibility)
  // =========================================================================

  test("dashboard-overview", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "Healthy" })).toBeVisible();
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "dashboard.png"),
      fullPage: true
    });
  });

  test("login-page", async ({ page }) => {
    await page.goto("/login");
    const loginHeading = page.getByRole("heading", { name: /login|chatty commander/i });
    await expect(loginHeading.first()).toBeVisible();
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, "login.png"),
      fullPage: true
    });
  });

  test("configuration-overview", async ({ page }) => {
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

  test("commands-list", async ({ page }) => {
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

  // =========================================================================
  // JOURNEY 1: FIRST-TIME SETUP (7 steps)
  // =========================================================================
  test.describe("Journey 1: First-Time Setup Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Initial landing and dashboard", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: /chatty commander|dashboard/i })).toBeVisible();
      await takeJourneyScreenshot(page, "setup", 1);
    });

    test("Step 2 - Navigate to configuration section", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/");
      await page.getByRole("link", { name: "Configuration" }).click();
      await expect(page).toHaveURL(/configuration/);
      await takeJourneyScreenshot(page, "setup", 2);
    });

    test("Step 3 - View advisor and provider settings", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      const advisorSection = page.locator("text=Advisors|text=Providers").first();
      if (await advisorSection.isVisible()) {
        await advisorSection.scrollIntoViewIfNeeded();
      }
      await takeJourneyScreenshot(page, "setup", 3);
    });

    test("Step 4 - Configure voice settings panel", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      const voiceSection = page.locator("text=Voice Settings|text=Voice|text=Enable Voice").first();
      if (await voiceSection.isVisible()) {
        await voiceSection.scrollIntoViewIfNeeded();
      }
      await takeJourneyScreenshot(page, "setup", 4);
    });

    test("Step 5 - Audio devices configuration", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      const audioHeading = page.locator("text=Audio Devices").first();
      if (await audioHeading.isVisible()) {
        await audioHeading.scrollIntoViewIfNeeded();
      }
      await takeJourneyScreenshot(page, "setup", 5);
    });

    test("Step 6 - Voice models ONNX selection", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      const modelsHeading = page.locator("text=Voice Models (ONNX)|text=Voice Models").first();
      if (await modelsHeading.isVisible()) {
        await modelsHeading.scrollIntoViewIfNeeded();
      }
      await takeJourneyScreenshot(page, "setup", 6);
    });

    test("Step 7 - Configuration saved successfully", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      const saveButton = page.getByRole("button", { name: /save|apply|ok/i }).first();
      if (await saveButton.isVisible()) {
        await saveButton.scrollIntoViewIfNeeded();
      }
      await takeJourneyScreenshot(page, "setup", 7);
    });
  });

  // =========================================================================
  // JOURNEY 2: CORE VOICE COMMAND FLOW (8 steps)
  // =========================================================================
  test.describe("Journey 2: Voice Command Execution Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Dashboard with voice enabled", async ({ page }) => {
      await mockDashboardAPIs(page);
      await mockVoiceCommandAPIs(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
      await takeJourneyScreenshot(page, "voice-flow", 1);
    });

    test("Step 2 - Navigate to commands list", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.goto("/");
      await page.getByRole("link", { name: "Commands" }).click();
      await expect(page.getByRole("heading", { name: /commands/i })).toBeVisible();
      await takeJourneyScreenshot(page, "voice-flow", 2);
    });

    test("Step 3 - Command authoring interface", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.route("**/api/v1/commands/generate", (route) =>
        route.fulfill({
          status: 200,
          json: {
            name: "open_notepad",
            display_name: "Open Notepad",
            description: "Opens Notepad application",
            actions: [
              { type: "keypress", keys: "win+r" },
              { type: "text", value: "notepad" },
            ],
          },
        })
      );
      await page.goto("/commands/authoring");
      await expect(page.getByRole("heading", { name: /command authoring|author/i })).toBeVisible();
      await takeJourneyScreenshot(page, "voice-flow", 3);
    });

    test("Step 4 - Command form with description filled", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.goto("/commands/authoring");
      const descriptionInput = page.locator("input, textarea").filter({ hasText: /description/i }).first();
      if (await descriptionInput.isVisible()) {
        await descriptionInput.fill("Opens Notepad application");
      }
      await takeJourneyScreenshot(page, "voice-flow", 4);
    });

    test("Step 5 - Command generated and displayed", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.route("**/api/v1/commands/generate", (route) =>
        route.fulfill({
          status: 200,
          json: {
            name: "open_notepad",
            display_name: "Open Notepad",
            description: "Opens Notepad application",
            actions: [{ type: "keypress", keys: "win+r" }],
          },
        })
      );
      await page.goto("/commands/authoring");
      await page.waitForTimeout(500);
      await takeJourneyScreenshot(page, "voice-flow", 5);
    });

    test("Step 6 - Return to commands list", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.goto("/commands");
      await expect(page.getByRole("heading", { name: /commands/i })).toBeVisible();
      await takeJourneyScreenshot(page, "voice-flow", 6);
    });

    test("Step 7 - Voice command execution confirmation", async ({ page }) => {
      await mockVoiceCommandAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(300);
      await takeJourneyScreenshot(page, "voice-flow", 7);
    });

    test("Step 8 - Dashboard with updated statistics", async ({ page }) => {
      await mockDashboardAPIs(page);
      await mockVoiceCommandAPIs(page);
      await page.goto("/");
      await expect(page.locator(".stat-value", { hasText: /1247|healthy/i }).first()).toBeVisible();
      await takeJourneyScreenshot(page, "voice-flow", 8);
    });
  });

  // =========================================================================
  // JOURNEY 3: WEB DASHBOARD INTERACTION (6 steps)
  // =========================================================================
  test.describe("Journey 3: Dashboard Interaction Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Fresh dashboard load", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
      await takeJourneyScreenshot(page, "dashboard", 1);
    });

    test("Step 2 - Dashboard with health statistics", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      const healthValue = page.locator(".stat-value", { hasText: "Healthy" });
      await expect(healthValue).toBeVisible();
      await takeJourneyScreenshot(page, "dashboard", 2);
    });

    test("Step 3 - Dashboard showing agent contexts", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "dashboard", 3);
    });

    test("Step 4 - Click to commands from dashboard", async ({ page }) => {
      await mockCommandsAPIs(page);
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.getByRole("link", { name: "Commands" }).click();
      await expect(page).toHaveURL(/commands/);
      await takeJourneyScreenshot(page, "dashboard", 4);
    });

    test("Step 5 - Return to dashboard from commands", async ({ page }) => {
      await mockDashboardAPIs(page);
      await mockCommandsAPIs(page);
      await page.goto("/commands");
      await page.getByRole("link", { name: "Dashboard" }).click();
      await expect(page).toHaveURL(/dashboard/);
      await takeJourneyScreenshot(page, "dashboard", 5);
    });

    test("Step 6 - Final dashboard state", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "dashboard", 6);
    });
  });

  // =========================================================================
  // JOURNEY 4: REAL-TIME FEATURES (5 steps)
  // =========================================================================
  test.describe("Journey 4: Real-Time Features Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Realtime status idle", async ({ page }) => {
      await page.route("**/api/v1/voice/status", (route) =>
        route.fulfill({
          status: 200,
          json: { is_listening: false, current_input: "", confidence: 0, timestamp: new Date().toISOString() }
        })
      );
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "realtime", 1);
    });

    test("Step 2 - Realtime status listening", async ({ page }) => {
      await page.route("**/api/v1/voice/status", (route) =>
        route.fulfill({ status: 200, json: MOCK_REALTIME_STATUS })
      );
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "realtime", 2);
    });

    test("Step 3 - Voice command recognized by system", async ({ page }) => {
      await mockVoiceCommandAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "realtime", 3);
    });

    test("Step 4 - Command execution in progress", async ({ page }) => {
      await page.route("**/api/v1/voice/command", (route) =>
        route.fulfill({
          status: 200,
          json: {
            ...MOCK_VOICE_COMMAND_RESPONSE,
            executed_at: new Date().toISOString(),
            execution_time_ms: 120
          }
        })
      );
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "realtime", 4);
    });

    test("Step 5 - Command execution completed", async ({ page }) => {
      await mockVoiceCommandAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(300);
      await takeJourneyScreenshot(page, "realtime", 5);
    });
  });

  // =========================================================================
  // JOURNEY 5: EDGE CASES & ERROR STATES (7 steps)
  // =========================================================================
  test.describe("Journey 5: Edge Cases & Error States", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Unhealthy service status", async ({ page }) => {
      await page.route("**/health", (route) =>
        route.fulfill({
          status: 200,
          json: {
            ...HEALTH_RESPONSE,
            status: "unhealthy",
            cpu_usage: "98.5",
            memory_usage: "99.1"
          }
        })
      );
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 1);
    });

    test("Step 2 - Voice service connection error state", async ({ page }) => {
      await mockErrorAPIs(page);
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 2);
    });

    test("Step 3 - Empty commands list state", async ({ page }) => {
      await page.route("**/api/v1/commands", (route) =>
        route.fulfill({ status: 200, json: [] })
      );
      await page.goto("/commands");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 3);
    });

    test("Step 4 - Configuration load failure", async ({ page }) => {
      await page.route("**/api/v1/config", (route) =>
        route.fulfill({ status: 500, json: { error: "Config load failed" } })
      );
      await page.goto("/configuration");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 4);
    });

    test("Step 5 - Network idle with no data available", async ({ page }) => {
      await page.route("**/health", (route) => route.abort());
      await page.route("**/api/v1/**", (route) => route.abort());
      await page.goto("/");
      await page.waitForTimeout(500);
      await takeJourneyScreenshot(page, "errors", 5);
    });

    test("Step 6 - Page not found 404 error", async ({ page }) => {
      await page.goto("/nonexistent-page");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 6);
    });

    test("Step 7 - Service degraded performance state", async ({ page }) => {
      await page.route("**/health", (route) =>
        route.fulfill({
          status: 200,
          json: {
            ...HEALTH_RESPONSE,
            status: "degraded",
            cpu_usage: "85.2",
            memory_usage: "88.7"
          }
        })
      );
      await page.goto("/");
      await page.waitForTimeout(200);
      await takeJourneyScreenshot(page, "errors", 7);
    });
  });

  // =========================================================================
  // JOURNEY 6: Agent Management Flow (8 steps)
  // Tests the new Agent Fleet Manager UI for creating and managing AI agents
  // =========================================================================
  test.describe("Journey 6: Agent Management Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Navigate to Agents Page", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.getByRole("link", { name: /agents|ai agents/i }).first().click();
      await expect(page).toHaveURL(/agents/);
      await expect(page.getByRole("heading", { name: /agents|manage agents/ })).toBeVisible();
      await takeJourneyScreenshot(page, "agents", 1);
    });

    test("Step 2 - View existing agent blueprints", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await expect(page.getByRole("heading")).toBeVisible();
      await takeJourneyScreenshot(page, "agents", 2);
    });

    test("Step 3 - Create new agent - form opened", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await page.getByRole("button", { name: /create|add|new/i }).first().click();
      await expect(page.getByRole("dialog") || page.locator("form")).toBeVisible();
      await takeJourneyScreenshot(page, "agents", 3);
    });

    test("Step 4 - Agent creation with persona details", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await page.getByRole("button", { name: /create|add|new/i }).first().click();
      await page.getByLabel(/name/i).fill("Research Assistant");
      await page.getByLabel(/description/i).fill("Helper for researching topics");
      await takeJourneyScreenshot(page, "agents", 4);
    });

    test("Step 5 - Configure agent capabilities", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await page.getByRole("button", { name: /create|add|new/i }).first().click();
      await page.getByLabel(/name/i).fill("Code Reviewer");
      await page.getByLabel(/capabilities|skills/i).first().click();
      await takeJourneyScreenshot(page, "agents", 5);
    });

    test("Step 6 - Assign team role to agent", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await page.getByRole("button", { name: /create|add|new/i }).first().click();
      await page.getByLabel(/name/i).fill("Team Lead");
      await page.getByLabel(/role|team/i).first().selectOption(/researcher|analyst|coder/);
      await takeJourneyScreenshot(page, "agents", 6);
    });

    test("Step 7 - Agent list with multiple agents", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await expect(page.getByRole("listitem").nth(2)).toBeVisible();
      await takeJourneyScreenshot(page, "agents", 7);
    });

    test("Step 8 - Agent detail view", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/agents");
      await page.getByRole("link").nth(2).click();
      await expect(page.getByRole("heading", { name: /research|code|team/ })).toBeVisible();
      await takeJourneyScreenshot(page, "agents", 8);
    });
  });


  // =========================================================================
  // JOURNEY 7: Configuration Management Flow (8 steps)
  // Tests comprehensive configuration settings and management
  // =========================================================================
  test.describe("Journey 7: Configuration Management Flow", () => {
    test.use({ viewport: { width: 1280, height: 900 } });

    test("Step 1 - Navigate to Configuration", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/");
      await page.getByRole("link", { name: /configuration|settings/i }).first().click();
      await expect(page).toHaveURL(/configuration/);
      await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();
      await takeJourneyScreenshot(page, "config", 1);
    });

    test("Step 2 - View general configuration settings", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await expect(page.getByRole("heading")).toBeVisible();
      await takeJourneyScreenshot(page, "config", 2);
    });

    test("Step 3 - Configure provider API settings", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByLabel(/api key|base url|model/i).first().click();
      await takeJourneyScreenshot(page, "config", 3);
    });

    test("Step 4 - Configure voice system settings", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByRole("tab", { name: /voice|audio/i }).first().click();
      await expect(page.getByRole("tabpanel")).toBeVisible();
      await takeJourneyScreenshot(page, "config", 4);
    });

    test("Step 5 - Configure audio input/output devices", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByRole("tab", { name: /voice|audio/i }).first().click();
      await page.getByRole("combobox", { name: /input|microphone/i }).first().selectOption();
      await takeJourneyScreenshot(page, "config", 5);
    });

    test("Step 6 - Configure voice wake word models", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByRole("tab", { name: /voice|wake word/i }).first().click();
      await expect(page.getByRole("tabpanel")).toBeVisible();
      await takeJourneyScreenshot(page, "config", 6);
    });

    test("Step 7 - Save configuration changes", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByRole("button", { name: /save|apply|update/i }).first().click();
      await takeJourneyScreenshot(page, "config", 7);
    });

    test("Step 8 - Verify configuration persistence", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await page.getByRole("link", { name: /dashboard/i }).first().click();
      await page.getByRole("link", { name: /configuration/i }).first().click();
      await takeJourneyScreenshot(page, "config", 8);
    });
  });
  // =========================================================================
  // MOBILE RESPONSIVE SCREENSHOTS (5 steps)
  // =========================================================================
  test.describe("Mobile Responsive Screenshots", () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test("Mobile - Dashboard view", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: /dashboard|chatty commander/i })).toBeVisible();
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: path.join(JOURNEYS_DIR, "mobile-dashboard.png"),
        fullPage: true
      });
    });

    test("Mobile - Commands list view", async ({ page }) => {
      await mockCommandsAPIs(page);
      await page.goto("/commands");
      await expect(page.getByRole("heading", { name: /commands/i })).toBeVisible();
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: path.join(JOURNEYS_DIR, "mobile-commands.png"),
        fullPage: true
      });
    });

    test("Mobile - Configuration view", async ({ page }) => {
      await mockConfigurationAPIs(page);
      await page.goto("/configuration");
      await expect(page.getByRole("heading", { name: /configuration/i })).toBeVisible();
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: path.join(JOURNEYS_DIR, "mobile-configuration.png"),
        fullPage: true
      });
    });

    test("Mobile - Setup journey step 1", async ({ page }) => {
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: path.join(JOURNEYS_DIR, "mobile-setup-1.png"),
        fullPage: true
      });
    });

    test("Mobile - Voice flow step 1", async ({ page }) => {
      await mockVoiceCommandAPIs(page);
      await mockDashboardAPIs(page);
      await page.goto("/");
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: path.join(JOURNEYS_DIR, "mobile-voice-flow-1.png"),
        fullPage: true
      });
    });
  });
});
