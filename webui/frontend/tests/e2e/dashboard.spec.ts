import { test, expect, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Shared mock data
// ---------------------------------------------------------------------------

const HEALTH_RESPONSE = {
  status: "healthy",
  uptime: "3d 12h 45m",
  commands_executed: 42,
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
  { name: "take_screenshot", description: "Captures screen" },
  { name: "cycle_window", description: "Cycles active window" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Set up all API route mocks that the dashboard depends on. */
async function mockDashboardAPIs(page: Page, overrides?: {
  health?: object | null;
  agents?: object | null;
  commands?: object | null;
}) {
  await page.route("**/health", (route) => {
    if (overrides?.health === null) {
      return route.fulfill({ status: 503, body: "Service Unavailable" });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(overrides?.health ?? HEALTH_RESPONSE),
    });
  });

  await page.route("**/api/v1/advisors/context/stats", (route) => {
    if (overrides?.agents === null) {
      return route.fulfill({ status: 500, body: "Internal Server Error" });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(overrides?.agents ?? AGENT_STATS_RESPONSE),
    });
  });

  await page.route("**/api/v1/commands", (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(overrides?.commands ?? COMMANDS_RESPONSE),
    });
  });
}

// ---------------------------------------------------------------------------
// Tests: Stats Cards
// ---------------------------------------------------------------------------

test.describe("Dashboard - Stats Cards", () => {
  test("renders all 6 stat cards with correct data from /health", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // System Status
    await expect(page.locator(".stat-title", { hasText: "System Status" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "Healthy" })).toBeVisible();

    // Uptime
    await expect(page.locator(".stat-title", { hasText: "Uptime" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "3d 12h 45m" })).toBeVisible();

    // Commands
    await expect(page.locator(".stat-title", { hasText: "Commands" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "42" })).toBeVisible();

    // CPU Load
    await expect(page.locator(".stat-title", { hasText: "CPU Load" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "23.5" })).toBeVisible();

    // Memory
    await expect(page.locator(".stat-title", { hasText: "Memory" })).toBeVisible();
    await expect(page.locator(".stat-value", { hasText: "61.2" })).toBeVisible();

    // WebSocket
    await expect(page.locator(".stat-title", { hasText: "WebSocket" })).toBeVisible();
  });

  test("shows fallback values when /health returns error", async ({ page }) => {
    await mockDashboardAPIs(page, { health: null });
    await page.goto("/dashboard");

    // Should still render the dashboard (query returns fallback data)
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 10000 });

    // Fallback: Unknown status, N/A for uptime, 0 for commands
    await expect(page.locator(".stat-value", { hasText: "Unknown" })).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Tests: Command Execution
// ---------------------------------------------------------------------------

test.describe("Dashboard - Command Execution", () => {
  // The command log's .mockup-code shares the class with agent card mockup-code
  // sections, so we scope to the card that contains the "Real-time Command Log" heading.
  const commandLogCard = (page: Page) =>
    page.locator(".card", { has: page.getByText("Real-time Command Log") });

  test("executes a command and shows it in the log", async ({ page }) => {
    await mockDashboardAPIs(page);

    // Mock the command execution endpoint
    await page.route("**/api/v1/command", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok", result: "Command executed" }),
        });
      }
      return route.continue();
    });

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // Wait for WebSocket to connect so the input is enabled
    const wsStatus = page.locator(".stat-value", { hasText: "Connected" });
    await expect(wsStatus).toBeVisible({ timeout: 15000 });

    const commandInput = page.getByLabel("Type and execute a command");
    const executeButton = page.getByRole("button", { name: /Execute/ });

    // Type and submit
    await commandInput.fill("take_screenshot");
    await expect(executeButton).toBeEnabled();
    await executeButton.click();

    // Verify the command appears in the log
    await expect(commandLogCard(page).locator(".mockup-code")).toContainText("> Executing: take_screenshot");

    // Input should be cleared after submission
    await expect(commandInput).toHaveValue("");
  });

  test("executes command on Enter key press", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.route("**/api/v1/command", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok" }),
        });
      }
      return route.continue();
    });

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // Wait for connected state
    await expect(page.locator(".stat-value", { hasText: "Connected" })).toBeVisible({ timeout: 15000 });

    const commandInput = page.getByLabel("Type and execute a command");
    await commandInput.fill("cycle_window");
    await commandInput.press("Enter");

    await expect(commandLogCard(page).locator(".mockup-code")).toContainText("> Executing: cycle_window");
  });

  test("does not execute with empty input", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // Wait for connected state
    await expect(page.locator(".stat-value", { hasText: "Connected" })).toBeVisible({ timeout: 15000 });

    const executeButton = page.getByRole("button", { name: /Execute/ });

    // Button should be disabled when input is empty
    await expect(executeButton).toBeDisabled();

    // Log should still show the "Waiting for commands..." placeholder
    await expect(commandLogCard(page).locator(".mockup-code")).toContainText("Waiting for commands...");
  });

  test("shows error in log when command execution fails", async ({ page }) => {
    await mockDashboardAPIs(page);

    await page.route("**/api/v1/command", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Internal server error" }),
        });
      }
      return route.continue();
    });

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // Wait for connected state
    await expect(page.locator(".stat-value", { hasText: "Connected" })).toBeVisible({ timeout: 15000 });

    const commandInput = page.getByLabel("Type and execute a command");
    await commandInput.fill("bad_command");
    await commandInput.press("Enter");

    // Should show the executing message first
    await expect(commandLogCard(page).locator(".mockup-code")).toContainText("> Executing: bad_command");

    // Should also show an error message (text-error styled)
    await expect(commandLogCard(page).locator(".mockup-code pre.text-error")).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// Tests: Performance Chart
// ---------------------------------------------------------------------------

test.describe("Dashboard - Performance Chart", () => {
  test("renders the performance chart section", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Real-time Performance History")).toBeVisible();

    // Chart container should be present
    await expect(page.locator(".recharts-wrapper")).toBeVisible({ timeout: 10000 });
  });

  test("pause and resume chart updates", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");
    await expect(page.getByText("Real-time Performance History")).toBeVisible();

    const pauseButton = page.getByLabel("Pause Chart");
    await expect(pauseButton).toBeVisible();

    // Click pause
    await pauseButton.click();

    // Now the button label should change to "Resume Chart"
    const resumeButton = page.getByLabel("Resume Chart");
    await expect(resumeButton).toBeVisible();

    // Click resume
    await resumeButton.click();

    // Should switch back to "Pause Chart"
    await expect(page.getByLabel("Pause Chart")).toBeVisible();
  });

  test("export CSV button is present and clickable", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");
    await expect(page.getByText("Real-time Performance History")).toBeVisible();

    const exportButton = page.getByLabel("Export Data as CSV");
    await expect(exportButton).toBeVisible();

    // Intercept the download to verify the export triggers
    const downloadPromise = page.waitForEvent("download", { timeout: 5000 }).catch(() => null);
    await exportButton.click();

    // The download may or may not fire depending on whether history data
    // has accumulated. We just verify the button is clickable without error.
    // If a download fires, verify the filename.
    const download = await downloadPromise;
    if (download) {
      expect(download.suggestedFilename()).toBe("performance_history.csv");
    }
  });
});

// ---------------------------------------------------------------------------
// Tests: Agent Cards
// ---------------------------------------------------------------------------

test.describe("Dashboard - Agent Cards", () => {
  test("displays agent cards with name and status badge", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");

    await expect(page.getByText("Agent Status")).toBeVisible();

    // Two agents from the mock data
    await expect(page.getByText("helperbot @ discord-advisor")).toBeVisible();
    await expect(page.getByText("streambot @ twitch-advisor")).toBeVisible();

    // Status badges should show "online"
    const badges = page.locator(".badge", { hasText: "online" });
    await expect(badges).toHaveCount(2);
  });

  test("shows empty state when no agents returned", async ({ page }) => {
    await mockDashboardAPIs(page, {
      agents: { contexts: {}, total: 0 },
    });
    await page.goto("/dashboard");

    await expect(page.getByText("Agent Status")).toBeVisible();

    // No agent cards should be rendered
    const agentCards = page.locator(".card-title", { hasText: /@ / });
    await expect(agentCards).toHaveCount(0);
  });

  test("agent cards display last sent, received, and content fields", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");

    await expect(page.getByText("helperbot @ discord-advisor")).toBeVisible();

    // Check for the field labels
    await expect(page.getByText("Last Sent").first()).toBeVisible();
    await expect(page.getByText("Last Received").first()).toBeVisible();
    await expect(page.getByText("Content").first()).toBeVisible();

    // Check that timestamps from mock data are rendered
    await expect(page.getByText("2026-03-26T10:00:00Z").first()).toBeVisible();
    await expect(page.getByText("discord-ctx-1")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Tests: WebSocket Status Indicator
// ---------------------------------------------------------------------------

test.describe("Dashboard - WebSocket Status", () => {
  test("shows Connected when WebSocket is active", async ({ page }) => {
    await mockDashboardAPIs(page);
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    // The real server is running in test-mode, so WS should connect
    const wsStatus = page.locator(".stat-value", { hasText: "Connected" });
    await expect(wsStatus).toBeVisible({ timeout: 15000 });
    await expect(wsStatus).toHaveClass(/text-success/);
  });

  test("shows Offline when WebSocket cannot connect", async ({ page }) => {
    await mockDashboardAPIs(page);

    // page.route() cannot intercept WebSocket upgrades, so we stub the
    // WebSocket constructor in the browser context before the page loads.
    await page.addInitScript(() => {
      const OriginalWebSocket = window.WebSocket;
      // @ts-ignore
      window.WebSocket = function (url: string, protocols?: string | string[]) {
        if (typeof url === "string" && url.includes("/ws")) {
          // Return a WebSocket-like object that immediately errors/closes
          const fake = new EventTarget() as any;
          fake.readyState = 3; // CLOSED
          fake.send = () => {};
          fake.close = () => {};
          fake.addEventListener = EventTarget.prototype.addEventListener;
          fake.removeEventListener = EventTarget.prototype.removeEventListener;
          // Fire error + close asynchronously so consumers attach handlers first
          setTimeout(() => {
            fake.dispatchEvent(new Event("error"));
            fake.readyState = 3;
            const closeEvent = new CloseEvent("close", { code: 1006, reason: "blocked" });
            if (fake.onerror) fake.onerror(new Event("error"));
            if (fake.onclose) fake.onclose(closeEvent);
            fake.dispatchEvent(closeEvent);
          }, 0);
          return fake;
        }
        return new OriginalWebSocket(url, protocols);
      } as any;
    });

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    const wsStatus = page.locator(".stat-value", { hasText: "Offline" });
    await expect(wsStatus).toBeVisible({ timeout: 10000 });
    await expect(wsStatus).toHaveClass(/text-error/);
  });
});

// ---------------------------------------------------------------------------
// Tests: Loading State
// ---------------------------------------------------------------------------

test.describe("Dashboard - Loading State", () => {
  test("shows loading skeleton while data is being fetched", async ({ page }) => {
    // Delay the health response to observe the loading state
    await page.route("**/health", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(HEALTH_RESPONSE),
      });
    });
    await page.route("**/api/v1/advisors/context/stats", (route) => {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(AGENT_STATS_RESPONSE),
      });
    });

    await page.goto("/dashboard");

    // Should show loading skeleton
    const skeleton = page.locator("[aria-busy='true'][aria-label='Loading dashboard']");
    await expect(skeleton).toBeVisible({ timeout: 3000 });

    // After the delayed response resolves, dashboard should render
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 10000 });
  });
});
