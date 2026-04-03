import { test, expect, Page } from "@playwright/test";

// ─── Shared mock data ────────────────────────────────────────────────────────

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
  input: ["Mock Microphone 1", "Mock Microphone 2"],
  output: ["Mock Speaker 1", "Mock Speaker 2", "HDMI Output"],
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
    {
      name: "chatty_wake_v1.onnx",
      path: "/models/chatty_wake_v1.onnx",
      size_bytes: 819200,
      size_human: "800.0 KB",
      modified: "2026-03-01T08:45:00Z",
      state: "chatty",
    },
  ],
  total_count: 3,
  total_size_bytes: 4399104,
  total_size_human: "4.2 MB",
};

const MOCK_LLM_MODELS = {
  data: [
    { id: "gpt-4o-mini" },
    { id: "llama-3.1-8b-instant" },
    { id: "mixtral-8x7b" },
  ],
};

/** Set up all API route mocks for the configuration page. */
async function mockAllRoutes(page: Page) {
  await page.route("**/api/v1/config", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, json: MOCK_CONFIG });
    }
    if (route.request().method() === "PUT") {
      return route.fulfill({ status: 200, json: { status: "ok" } });
    }
    return route.continue();
  });

  await page.route("**/api/v1/audio/devices", (route) =>
    route.fulfill({ status: 200, json: MOCK_AUDIO_DEVICES }),
  );

  await page.route("**/api/v1/audio/device", (route) =>
    route.fulfill({ status: 200, json: { status: "ok" } }),
  );

  await page.route("**/api/v1/models/files/*", (route) => {
    if (route.request().method() === "DELETE") {
      return route.fulfill({ status: 200, json: { status: "deleted" } });
    }
    return route.continue();
  });

  await page.route("**/api/v1/models/files", (route) =>
    route.fulfill({ status: 200, json: MOCK_VOICE_MODELS }),
  );

  await page.route("**/api/v1/models/upload", (route) =>
    route.fulfill({ status: 200, json: { status: "uploaded" } }),
  );

  // Mock the LLM /models endpoint (called via fetchLLMModels -> baseUrl + "/models")
  await page.route("**/v1/models", (route) =>
    route.fulfill({ status: 200, json: MOCK_LLM_MODELS }),
  );

  // Catch advisor stats to prevent errors
  await page.route("**/api/v1/advisors/**", (route) =>
    route.fulfill({ status: 200, json: { contexts: {}, total: 0 } }),
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Locate the inner card-body for an audio device card by its card-title text. */
function audioCardBody(page: Page, heading: string) {
  return page.locator(".card-body").filter({
    has: page.locator(".card-title", { hasText: heading }),
  });
}

/** Locate the "Fetch list" button inside the LLM section (inside a <label>). */
function fetchListBtn(page: Page) {
  return page.locator("button", { hasText: "Fetch list" });
}

// ─── Theme Dropdown ──────────────────────────────────────────────────────────

test.describe("Configuration Page - Theme Dropdown", () => {
  test("renders with default dark theme selected", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const themeSelect = page.locator('select[name="theme"]');
    await expect(themeSelect).toBeVisible();
    await expect(themeSelect).toHaveValue("dark");
  });

  test("can select each theme option", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const themeSelect = page.locator('select[name="theme"]');
    await expect(themeSelect).toBeVisible();

    for (const theme of ["light", "cyberpunk", "synthwave", "dark"]) {
      await themeSelect.selectOption(theme);
      await expect(themeSelect).toHaveValue(theme);
    }
  });

  test("theme change is reflected in the document data-theme attribute", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const themeSelect = page.locator('select[name="theme"]');

    await themeSelect.selectOption("cyberpunk");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "cyberpunk");

    await themeSelect.selectOption("synthwave");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "synthwave");

    await themeSelect.selectOption("light");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  });
});

// ─── Service Toggles ─────────────────────────────────────────────────────────

test.describe("Configuration Page - Service Toggles", () => {
  test("displays Voice Commands and REST API toggles", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const voiceToggle = page.locator('input[name="voiceCommands"]');
    const restToggle = page.locator('input[name="restApi"]');

    await expect(voiceToggle).toBeVisible();
    await expect(restToggle).toBeVisible();

    // Both should be checked by default per mock config
    await expect(voiceToggle).toBeChecked();
    await expect(restToggle).toBeChecked();
  });

  test("can toggle Voice Commands off and on", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const voiceToggle = page.locator('input[name="voiceCommands"]');
    await expect(voiceToggle).toBeChecked();

    await voiceToggle.uncheck();
    await expect(voiceToggle).not.toBeChecked();

    await voiceToggle.check();
    await expect(voiceToggle).toBeChecked();
  });

  test("can toggle REST API off and on", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const restToggle = page.locator('input[name="restApi"]');
    await expect(restToggle).toBeChecked();

    await restToggle.uncheck();
    await expect(restToggle).not.toBeChecked();

    await restToggle.check();
    await expect(restToggle).toBeChecked();
  });
});

// ─── Audio Devices ───────────────────────────────────────────────────────────

test.describe("Configuration Page - Audio Devices", () => {
  test("populates input device dropdown from mock API", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const audioSection = page.locator("h3", { hasText: "Audio Devices" });
    await expect(audioSection).toBeVisible();

    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const inputSelect = inputCardBody.locator("select");
    await expect(inputSelect).toBeVisible();
    await expect(inputSelect).toContainText("Mock Microphone 1");
    await expect(inputSelect).toContainText("Mock Microphone 2");
  });

  test("populates output device dropdown from mock API", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const outputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Output Device" }) });
    const outputSelect = outputCardBody.locator("select");
    await expect(outputSelect).toBeVisible();
    await expect(outputSelect).toContainText("Mock Speaker 1");
    await expect(outputSelect).toContainText("Mock Speaker 2");
    await expect(outputSelect).toContainText("HDMI Output");
  });

  test("can select an input device", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const inputSelect = inputCardBody.locator("select");
    await expect(inputSelect).toContainText("Mock Microphone 1");

    await inputSelect.selectOption("Mock Microphone 2");
    await expect(inputSelect).toHaveValue("Mock Microphone 2");
  });

  test("can select an output device", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const outputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Output Device" }) });
    const outputSelect = outputCardBody.locator("select");
    await expect(outputSelect).toContainText("HDMI Output");

    await outputSelect.selectOption("HDMI Output");
    await expect(outputSelect).toHaveValue("HDMI Output");
  });

  test("Test button for input device is disabled when no device is selected", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const testBtn = inputCardBody.getByRole("button", { name: "Test" });
    await expect(testBtn).toBeVisible();
    await expect(testBtn).toBeDisabled();
  });

  test("Test button for input device becomes enabled after selecting a device", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const inputSelect = inputCardBody.locator("select");
    const testBtn = inputCardBody.getByRole("button", { name: "Test" });

    await expect(testBtn).toBeDisabled();
    await inputSelect.selectOption("Mock Microphone 1");
    await expect(testBtn).toBeEnabled();
  });

  test("clicking Test on input device shows Testing state and recovers", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const inputSelect = inputCardBody.locator("select");
    await inputSelect.selectOption("Mock Microphone 1");

    const testBtn = inputCardBody.getByRole("button", { name: "Test" });
    await testBtn.click();

    // Should show "Testing..." text while mic test is active
    await expect(inputCardBody.getByText("Testing...")).toBeVisible();

    // After the 3s timeout it should revert back to "Test"
    await expect(inputCardBody.getByRole("button", { name: "Test" })).toBeVisible({ timeout: 5000 });
  });

  test("Test button for output device is disabled when no device is selected", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const outputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Output Device" }) });
    const testBtn = outputCardBody.getByRole("button", { name: "Test" });
    await expect(testBtn).toBeDisabled();
  });

  test("clicking Test on output device shows Playing state and recovers", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const outputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Output Device" }) });
    const outputSelect = outputCardBody.locator("select");
    await outputSelect.selectOption("Mock Speaker 1");

    const testBtn = outputCardBody.getByRole("button", { name: "Test" });
    await testBtn.click();

    await expect(outputCardBody.getByText("Playing...")).toBeVisible();

    // After the 2s timeout it should revert
    await expect(outputCardBody.getByRole("button", { name: "Test" })).toBeVisible({ timeout: 4000 });
  });
});

// ─── Voice Models (ONNX) ────────────────────────────────────────────────────

test.describe("Configuration Page - Voice Models (ONNX)", () => {
  test("displays voice model table with mock data", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const modelsSection = page.locator("h3", { hasText: "Voice Models (ONNX)" });
    await expect(modelsSection).toBeVisible();

    // Verify table headers
    const table = page.locator("table");
    await expect(table.locator("th", { hasText: "Name" })).toBeVisible();
    await expect(table.locator("th", { hasText: "State" })).toBeVisible();
    await expect(table.locator("th", { hasText: "Size" })).toBeVisible();
    await expect(table.locator("th", { hasText: "Actions" })).toBeVisible();
  });

  test("shows model names, states, and sizes from mock data", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const table = page.locator("table");

    // Check each model row
    await expect(table.getByText("hey_jarvis_v0.1.onnx")).toBeVisible();
    await expect(table.getByText("ok_computer_v2.onnx")).toBeVisible();
    await expect(table.getByText("chatty_wake_v1.onnx")).toBeVisible();

    // Check state badges (use .badge selector to avoid matching model file names)
    await expect(table.locator(".badge", { hasText: "idle" })).toBeVisible();
    await expect(table.locator(".badge", { hasText: "computer" })).toBeVisible();
    await expect(table.locator(".badge", { hasText: "chatty" })).toBeVisible();

    // Check sizes
    await expect(table.getByText("1.4 MB")).toBeVisible();
    await expect(table.getByText("2.0 MB")).toBeVisible();
    await expect(table.getByText("800.0 KB")).toBeVisible();
  });

  test("shows empty state when no models exist", async ({ page }) => {
    await page.route("**/api/v1/config", (route) =>
      route.fulfill({ status: 200, json: MOCK_CONFIG }),
    );
    await page.route("**/api/v1/audio/devices", (route) =>
      route.fulfill({ status: 200, json: MOCK_AUDIO_DEVICES }),
    );
    await page.route("**/api/v1/models/files", (route) =>
      route.fulfill({
        status: 200,
        json: { models: [], total_count: 0, total_size_bytes: 0, total_size_human: "0 B" },
      }),
    );
    await page.route("**/api/v1/advisors/**", (route) =>
      route.fulfill({ status: 200, json: { contexts: {}, total: 0 } }),
    );

    await page.goto("/configuration");

    await expect(page.getByText("No custom models found.")).toBeVisible();
  });

  test("clicking delete button sends DELETE request for the correct model", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const table = page.locator("table");
    await expect(table.getByText("hey_jarvis_v0.1.onnx")).toBeVisible();

    const deleteBtn = page.getByRole("button", { name: "Delete model hey_jarvis_v0.1.onnx" });
    await expect(deleteBtn).toBeVisible();

    const deletePromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/models/files/hey_jarvis_v0.1.onnx") && req.method() === "DELETE",
    );

    await deleteBtn.click();
    const deleteReq = await deletePromise;
    expect(deleteReq.method()).toBe("DELETE");
  });

  test("upload section shows target state dropdown with correct options", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const uploadSection = page.locator("h4", { hasText: "Upload Model" });
    await expect(uploadSection).toBeVisible();

    const stateSelect = page.locator("select").filter({ hasText: "Idle (Wake Word)" });
    await expect(stateSelect).toBeVisible();

    // Verify all options exist
    const options = await stateSelect.locator("option").allInnerTexts();
    expect(options).toContain("Idle (Wake Word)");
    expect(options).toContain("Computer (Active)");
    expect(options).toContain("Chatty (Conv.)");
  });

  test("can change target state for upload", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const stateSelect = page.locator("select").filter({ hasText: "Idle (Wake Word)" });
    await stateSelect.selectOption("computer");
    await expect(stateSelect).toHaveValue("computer");

    await stateSelect.selectOption("chatty");
    await expect(stateSelect).toHaveValue("chatty");
  });

  test("file input accepts .onnx files and triggers upload", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const uploadPromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/models/upload") && req.method() === "POST",
    );

    const fileInput = page.getByLabel("Select ONNX voice model file");
    await expect(fileInput).toBeVisible();

    // Create a fake .onnx file and upload it
    await fileInput.setInputFiles({
      name: "my_custom_wake.onnx",
      mimeType: "application/octet-stream",
      buffer: Buffer.from("fake-onnx-model-data"),
    });

    const uploadReq = await uploadPromise;
    expect(uploadReq.method()).toBe("POST");
    // Verify the request contains multipart form data
    expect(uploadReq.headers()["content-type"]).toContain("multipart/form-data");
  });
});

// ─── LLM Endpoint ────────────────────────────────────────────────────────────

test.describe("Configuration Page - LLM Endpoint", () => {
  test("displays API Base URL and API Key inputs with defaults", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const llmSection = page.locator("h3", { hasText: "LLM Endpoint" });
    await expect(llmSection).toBeVisible();

    const baseUrlInput = page.locator('input[name="llmBaseUrl"]');
    await expect(baseUrlInput).toBeVisible();
    await expect(baseUrlInput).toHaveValue("http://localhost:11434/v1");

    const apiKeyInput = page.locator('input[name="apiKey"]');
    await expect(apiKeyInput).toBeVisible();
  });

  test("can fill in API Base URL", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const baseUrlInput = page.locator('input[name="llmBaseUrl"]');
    await baseUrlInput.clear();
    await baseUrlInput.fill("https://api.openai.com/v1");
    await expect(baseUrlInput).toHaveValue("https://api.openai.com/v1");
  });

  test("can fill in API Key", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const apiKeyInput = page.locator('input[name="apiKey"]');
    await apiKeyInput.fill("sk-test-key-12345");
    await expect(apiKeyInput).toHaveValue("sk-test-key-12345");
  });

  test("displays model text input when no models have been fetched", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    // Before fetching, should show a text input for model (not a select)
    const modelInput = page.locator('input[name="llmModel"]');
    await expect(modelInput).toBeVisible();
  });

  test("Fetch Models button populates model dropdown", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const fetchBtn = page.locator("button", { hasText: "Fetch list" });
    await expect(fetchBtn).toBeVisible();

    await fetchBtn.click();

    // After fetching, a <select> should appear with the model options
    const modelSelect = page.locator('select[name="llmModel"]');
    await expect(modelSelect).toBeVisible({ timeout: 5000 });

    // Wait for options to be populated
    await expect(modelSelect.locator("option").filter({ hasText: "gpt-4o-mini" })).toBeAttached({ timeout: 5000 });

    const options = await modelSelect.locator("option").allInnerTexts();
    expect(options).toContain("gpt-4o-mini");
    expect(options).toContain("llama-3.1-8b-instant");
    expect(options).toContain("mixtral-8x7b");
  });

  test("can select a model from the fetched dropdown", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    // Fetch models first
    await page.locator("button", { hasText: "Fetch list" }).click();

    const modelSelect = page.locator('select[name="llmModel"]');
    await expect(modelSelect).toBeVisible({ timeout: 5000 });

    // Wait for options to be populated
    await expect(modelSelect.locator("option").filter({ hasText: "gpt-4o-mini" })).toBeAttached({ timeout: 5000 });

    await modelSelect.selectOption("gpt-4o-mini");
    await expect(modelSelect).toHaveValue("gpt-4o-mini");

    await modelSelect.selectOption("mixtral-8x7b");
    await expect(modelSelect).toHaveValue("mixtral-8x7b");
  });

  test("Fetch Models button is disabled when base URL is empty", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const baseUrlInput = page.locator('input[name="llmBaseUrl"]');
    await baseUrlInput.clear();

    const fetchBtn = page.locator("button", { hasText: "Fetch list" });
    await expect(fetchBtn).toBeDisabled();
  });
});

// ─── Save Changes ────────────────────────────────────────────────────────────

test.describe("Configuration Page - Save Changes", () => {
  test("Save Changes button is visible and clickable", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    const saveBtn = page.getByRole("button", { name: "Save Changes" });
    await expect(saveBtn).toBeVisible();
    await expect(saveBtn).toBeEnabled();
  });

  test("clicking Save sends PUT /api/v1/config with current settings", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    // Wait for config to load
    await expect(page.locator('select[name="theme"]')).toHaveValue("dark");

    const savePromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/config") && req.method() === "PUT",
    );

    await page.getByRole("button", { name: "Save Changes" }).click();

    const saveReq = await savePromise;
    const body = saveReq.postDataJSON();

    expect(body).toHaveProperty("advisors");
    expect(body).toHaveProperty("ui");
    expect(body).toHaveProperty("voice");
    expect(body).toHaveProperty("services");
    expect(body.ui.theme).toBe("dark");
  });

  test("shows success indicator after saving", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    await expect(page.locator('select[name="theme"]')).toHaveValue("dark");

    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByText("Saved")).toBeVisible({ timeout: 5000 });
  });

  test("saves modified theme and service toggle values", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    // Wait for initial load
    await expect(page.locator('select[name="theme"]')).toHaveValue("dark");

    // Change theme
    await page.locator('select[name="theme"]').selectOption("cyberpunk");

    // Toggle voice commands off
    await page.locator('input[name="voiceCommands"]').uncheck();

    const savePromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/config") && req.method() === "PUT",
    );

    await page.getByRole("button", { name: "Save Changes" }).click();

    const saveReq = await savePromise;
    const body = saveReq.postDataJSON();

    expect(body.ui.theme).toBe("cyberpunk");
    expect(body.voice.enabled).toBe(false);
    expect(body.services.voiceCommands).toBe(false);
    expect(body.services.restApi).toBe(true);
  });

  test("saves audio device selection alongside config", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    // Select an input device
    const inputCardBody = page.locator(".card.shadow-sm").filter({ has: page.getByRole("heading", { name: "Input Device" }) });
    const inputSelect = inputCardBody.locator("select");
    await expect(inputSelect).toContainText("Mock Microphone 1");
    await inputSelect.selectOption("Mock Microphone 1");

    // Save should trigger both PUT /config and POST /audio/device
    const configPromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/config") && req.method() === "PUT",
    );
    const audioPromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/audio/device") && req.method() === "POST",
    );

    await page.getByRole("button", { name: "Save Changes" }).click();

    const configReq = await configPromise;
    expect(configReq.method()).toBe("PUT");

    const audioReq = await audioPromise;
    expect(audioReq.postDataJSON()).toEqual({ device_id: "Mock Microphone 1" });
  });
});

// ─── Page-level rendering ────────────────────────────────────────────────────

test.describe("Configuration Page - General", () => {
  test("renders the page heading and all section titles", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");

    await expect(page.getByRole("heading", { name: "Configuration" })).toBeVisible();
    await expect(page.getByText("General Settings")).toBeVisible();
    await expect(page.getByText("Services")).toBeVisible();
    await expect(page.getByText("Audio Devices")).toBeVisible();
    await expect(page.getByText("Voice Models (ONNX)")).toBeVisible();
    await expect(page.getByText("LLM Endpoint")).toBeVisible();
  });
});
