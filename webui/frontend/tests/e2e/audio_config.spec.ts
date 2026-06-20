import { test, expect, Page } from "@playwright/test";

// The Configuration page is now tabbed (General / Audio / Voice Models / LLM)
// and audio device selections are persisted as part of the unified
// PUT /api/v1/config payload (under `audio_settings`) rather than via a
// separate POST /api/v1/audio/device call. The Save button lives in a sticky
// bar, is disabled until the form is dirty, and is labelled "Saved" when clean
// and "Save Changes" once a change is made.

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
  audio_settings: { input_device: "", output_device: "" },
  _env_overrides: { api_key: false, base_url: false, model: false },
};

const MOCK_AUDIO_DEVICES = {
  input: ["Mock Microphone 1", "Mock Microphone 2"],
  output: ["Mock Speaker 1", "Mock Speaker 2"],
};

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

  await page.route("**/api/v1/models/files", (route) =>
    route.fulfill({
      status: 200,
      json: { models: [], total_count: 0, total_size_bytes: 0, total_size_human: "0 B" },
    }),
  );

  await page.route("**/api/v1/advisors/**", (route) =>
    route.fulfill({ status: 200, json: { contexts: {}, total: 0 } }),
  );
}

/** Open the Audio tab — its panel is only mounted while the tab is active. */
async function openAudioTab(page: Page) {
  await page.getByRole("tab", { name: "Audio" }).click();
}

test.describe("Audio Configuration", () => {
  test("fetches audio devices on load and populates the input select", async ({ page }) => {
    await mockAllRoutes(page);

    const requestPromise = page.waitForRequest((req) =>
      req.url().includes("/api/v1/audio/devices"),
    );

    await page.goto("/configuration");

    const request = await requestPromise;
    const response = await request.response();
    expect(response?.status()).toBe(200);

    // Audio device controls live under the Audio tab now.
    await openAudioTab(page);

    const audioDevicesSection = page.locator("h3", { hasText: "Audio Devices" });
    await expect(audioDevicesSection).toBeVisible();

    // The input <select> has a real label/id; address it via getByLabel.
    const inputSelect = page.getByLabel("Audio input device");
    await expect(inputSelect).toBeVisible();
    await expect(inputSelect).toContainText("Mock Microphone 1");

    const options = await inputSelect.locator("option").allInnerTexts();
    expect(options).toContain("Select device...");
    expect(options).toContain("Mock Microphone 1");
  });

  test("selecting an input device persists it via PUT /api/v1/config", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");
    await openAudioTab(page);

    const inputSelect = page.getByLabel("Audio input device");
    await expect(inputSelect).toContainText("Mock Microphone 1");
    await inputSelect.selectOption({ label: "Mock Microphone 1" });
    await expect(inputSelect).toHaveValue("Mock Microphone 1");

    // Making a change dirties the form; the Save button is now enabled and
    // relabelled "Save Changes".
    const saveBtn = page.getByTestId("save-button");
    await expect(saveBtn).toBeEnabled();
    await expect(saveBtn).toHaveText(/Save Changes/);

    // The device is saved as part of the unified config PUT (no separate
    // POST /api/v1/audio/device endpoint exists anymore).
    const saveRequestPromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/config") && req.method() === "PUT",
    );
    await saveBtn.click();

    const saveRequest = await saveRequestPromise;
    const body = saveRequest.postDataJSON();
    expect(body.audio_settings.input_device).toBe("Mock Microphone 1");

    const saveResponse = await saveRequest.response();
    expect(saveResponse?.status()).toBe(200);
  });

  test("selecting an output device persists it via PUT /api/v1/config", async ({ page }) => {
    await mockAllRoutes(page);
    await page.goto("/configuration");
    await openAudioTab(page);

    const outputSelect = page.getByLabel("Audio output device");
    await expect(outputSelect).toContainText("Mock Speaker 1");
    await outputSelect.selectOption({ label: "Mock Speaker 2" });
    await expect(outputSelect).toHaveValue("Mock Speaker 2");

    const saveRequestPromise = page.waitForRequest(
      (req) => req.url().includes("/api/v1/config") && req.method() === "PUT",
    );
    await page.getByTestId("save-button").click();

    const saveRequest = await saveRequestPromise;
    const body = saveRequest.postDataJSON();
    expect(body.audio_settings.output_device).toBe("Mock Speaker 2");
  });
});
