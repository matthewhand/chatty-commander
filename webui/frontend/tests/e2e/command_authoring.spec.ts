import { test, expect } from "@playwright/test";

// --- Shared Fixtures ---

const MOCK_GENERATED_COMMAND = {
  name: "start_my_day",
  display_name: "Start My Day",
  wakeword: "start my day",
  actions: [
    { type: "shell", cmd: "code ~/projects" },
    { type: "url", url: "https://mail.google.com" },
    { type: "keypress", keys: "ctrl+alt+t" },
  ],
};

const MOCK_CONFIG = {
  commands: {
    take_screenshot: {
      action: "shell",
      cmd: "gnome-screenshot",
    },
  },
  settings: {},
};

/**
 * Set up route mocks that most tests need: the auth/session endpoint
 * and the GET /api/v1/config endpoint used during save.
 */
async function setupBaseMocks(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/config", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_CONFIG),
      });
    } else if (route.request().method() === "PUT") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok" }),
      });
    } else {
      await route.continue();
    }
  });
}

// --- Test Suites ---

test.describe("Command Authoring - Mode Switching", () => {
  test("AI Mode tab is selected by default", async ({ page }) => {
    await page.goto("/commands/authoring");

    const aiTab = page.getByRole("tab", { name: /AI Mode/i });
    const manualTab = page.getByRole("tab", { name: /Manual Mode/i });

    await expect(aiTab).toHaveAttribute("aria-selected", "true");
    await expect(manualTab).toHaveAttribute("aria-selected", "false");
  });

  test("clicking Manual Mode tab switches to manual panel", async ({ page }) => {
    await page.goto("/commands/authoring");

    const manualTab = page.getByRole("tab", { name: /Manual Mode/i });
    await manualTab.click();

    await expect(manualTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("tab", { name: /AI Mode/i })).toHaveAttribute(
      "aria-selected",
      "false"
    );

    // Manual mode panel should be visible with its heading
    await expect(page.getByText("Manual Command Editor")).toBeVisible();
  });

  test("clicking AI Mode tab switches back to AI panel", async ({ page }) => {
    await page.goto("/commands/authoring");

    // Switch to manual first
    await page.getByRole("tab", { name: /Manual Mode/i }).click();
    await expect(page.getByText("Manual Command Editor")).toBeVisible();

    // Switch back to AI
    const aiTab = page.getByRole("tab", { name: /AI Mode/i });
    await aiTab.click();

    await expect(aiTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByText("Describe Your Command")).toBeVisible();
  });
});

test.describe("Command Authoring - AI Mode Flow", () => {
  test("Generate Command button is disabled when textarea is empty", async ({ page }) => {
    await page.goto("/commands/authoring");

    const generateBtn = page.getByRole("button", { name: /Generate Command/i });
    await expect(generateBtn).toBeDisabled();
  });

  test("Generate Command button enables when description is entered", async ({ page }) => {
    await page.goto("/commands/authoring");

    const textarea = page.getByPlaceholder(/When I say.*start my day/);
    await textarea.fill("Open my email and code editor");

    const generateBtn = page.getByRole("button", { name: /Generate Command/i });
    await expect(generateBtn).toBeEnabled();
  });

  test("generates command and shows preview on successful API call", async ({ page }) => {
    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    const textarea = page.getByPlaceholder(/When I say.*start my day/);
    await textarea.fill("start my day workflow");

    await page.getByRole("button", { name: /Generate Command/i }).click();

    // Verify generated command preview shows all fields
    await expect(page.getByText("Generated Command").first()).toBeVisible();
    await expect(page.getByText("start_my_day")).toBeVisible();
    await expect(page.getByText("Start My Day", { exact: true })).toBeVisible();
    await expect(page.getByText("start my day", { exact: true })).toBeVisible();

    // Verify actions are shown
    await expect(page.getByText("code ~/projects")).toBeVisible();
    await expect(page.getByText("https://mail.google.com")).toBeVisible();
    await expect(page.getByText("ctrl+alt+t")).toBeVisible();

    // Verify action type badges
    await expect(page.getByText("shell").first()).toBeVisible();
    await expect(page.getByText("url").first()).toBeVisible();
    await expect(page.getByText("keypress").first()).toBeVisible();
  });

  test("Regenerate button triggers a new API call", async ({ page }) => {
    let callCount = 0;

    await page.route("**/api/v1/commands/generate", async (route) => {
      callCount++;
      const command = {
        ...MOCK_GENERATED_COMMAND,
        name: callCount === 1 ? "start_my_day" : "start_my_day_v2",
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(command),
      });
    });

    await page.goto("/commands/authoring");

    const textarea = page.getByPlaceholder(/When I say.*start my day/);
    await textarea.fill("start my day workflow");

    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("start_my_day")).toBeVisible();

    // Click Regenerate
    await page.getByRole("button", { name: /Regenerate/i }).click();
    await expect(page.getByText("start_my_day_v2")).toBeVisible();

    expect(callCount).toBe(2);
  });

  test("Edit Manually button switches to manual mode with data pre-filled", async ({ page }) => {
    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    const textarea = page.getByPlaceholder(/When I say.*start my day/);
    await textarea.fill("start my day workflow");

    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").first()).toBeVisible();

    // Click "Edit Manually"
    await page.getByRole("button", { name: /Edit Manually/i }).click();

    // Should switch to manual mode
    await expect(page.getByRole("tab", { name: /Manual Mode/i })).toHaveAttribute(
      "aria-selected",
      "true"
    );

    // Fields should be pre-filled
    await expect(page.getByPlaceholder("my_command")).toHaveValue("start_my_day");
    await expect(page.getByPlaceholder("My Command")).toHaveValue("Start My Day");
    await expect(page.getByPlaceholder("Trigger phrase")).toHaveValue("start my day");

    // Actions should be carried over (3 actions)
    const removeButtons = page.getByRole("button", { name: "Remove action" });
    await expect(removeButtons).toHaveCount(3);
  });
});

test.describe("Command Authoring - Manual Mode Flow", () => {
  test("can fill in all command fields", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    const nameInput = page.getByPlaceholder("my_command");
    const displayInput = page.getByPlaceholder("My Command");
    const wakewordInput = page.getByPlaceholder("Trigger phrase");

    await nameInput.fill("test_command");
    await displayInput.fill("Test Command");
    await wakewordInput.fill("run test");

    await expect(nameInput).toHaveValue("test_command");
    await expect(displayInput).toHaveValue("Test Command");
    await expect(wakewordInput).toHaveValue("run test");
  });

  test("Add Action button adds a new action with default type keypress", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Initially no actions
    await expect(page.getByText('No actions defined yet')).toBeVisible();

    await page.getByRole("button", { name: /Add Action/i }).click();

    // Action 1 should appear
    await expect(page.getByText("Action 1")).toBeVisible();
    // Default type should be keypress selected in dropdown
    const typeSelect = page.locator("select").first();
    await expect(typeSelect).toHaveValue("keypress");
  });

  test("can select different action types and fill type-specific fields", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Add action and select URL type
    await page.getByRole("button", { name: /Add Action/i }).click();
    const typeSelect = page.locator("select").first();
    await typeSelect.selectOption("url");

    const urlInput = page.getByPlaceholder("https://example.com");
    await expect(urlInput).toBeVisible();
    await urlInput.fill("https://test.com");
    await expect(urlInput).toHaveValue("https://test.com");

    // Switch to shell type
    await typeSelect.selectOption("shell");
    const cmdInput = page.getByPlaceholder("e.g., npm start");
    await expect(cmdInput).toBeVisible();

    // Switch to custom_message type
    await typeSelect.selectOption("custom_message");
    const msgInput = page.getByPlaceholder("Enter message to display");
    await expect(msgInput).toBeVisible();

    // Switch to keypress type
    await typeSelect.selectOption("keypress");
    const keysInput = page.getByPlaceholder("e.g., ctrl+alt+t");
    await expect(keysInput).toBeVisible();
  });

  test("Remove action button removes the action", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Add two actions
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.getByRole("button", { name: /Add Action/i }).click();

    await expect(page.getByText("Action 1")).toBeVisible();
    await expect(page.getByText("Action 2")).toBeVisible();

    // Remove the first action
    const removeButtons = page.getByRole("button", { name: "Remove action" });
    await removeButtons.first().click();

    // Only one action should remain
    await expect(page.getByText("Action 1")).toBeVisible();
    await expect(page.getByText("Action 2")).not.toBeVisible();
  });

  test("adding multiple actions of different types works correctly", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Add a shell action
    await page.getByRole("button", { name: /Add Action/i }).click();
    const firstSelect = page.locator("select").first();
    await firstSelect.selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("echo hello");

    // Add a URL action
    await page.getByRole("button", { name: /Add Action/i }).click();
    const secondSelect = page.locator("select").nth(1);
    await secondSelect.selectOption("url");
    await page.getByPlaceholder("https://example.com").fill("https://example.org");

    await expect(page.getByText("Action 1")).toBeVisible();
    await expect(page.getByText("Action 2")).toBeVisible();
  });
});

test.describe("Command Authoring - Save Flow", () => {
  test("Save Command opens confirmation modal with command summary", async ({ page }) => {
    await setupBaseMocks(page);

    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    // Generate a command via AI
    await page.getByPlaceholder(/When I say.*start my day/).fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").first()).toBeVisible();

    // Click Save Command
    await page.getByRole("button", { name: /Save Command/i }).click();

    // Confirmation modal should appear
    await expect(page.getByText("Confirm Command Creation")).toBeVisible();

    // Command summary should be in modal
    await expect(page.getByText("start_my_day").nth(1)).toBeVisible();
    await expect(page.getByText("Start My Day").nth(1)).toBeVisible();

    // Actions count should be shown
    await expect(page.getByText(/Actions \(3\)/)).toBeVisible();
  });

  test("Cancel button in confirmation modal dismisses it", async ({ page }) => {
    await setupBaseMocks(page);

    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder(/When I say.*start my day/).fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").first()).toBeVisible();

    await page.getByRole("button", { name: /Save Command/i }).click();
    await expect(page.getByText("Confirm Command Creation")).toBeVisible();

    // Click Cancel
    await page.getByRole("button", { name: "Cancel" }).click();

    // Modal should be dismissed
    await expect(page.getByText("Confirm Command Creation")).not.toBeVisible();

    // The generated command preview should still be visible
    await expect(page.getByText("Generated Command").first()).toBeVisible();
  });

  test("Confirm Save calls PUT /api/v1/config and resets form", async ({ page }) => {
    let putCalled = false;

    await page.route("**/api/v1/config", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_CONFIG),
        });
      } else if (route.request().method() === "PUT") {
        putCalled = true;
        const body = JSON.parse(route.request().postData() || "{}");
        // Verify the new command is included in the PUT body
        expect(body.commands).toHaveProperty("start_my_day");
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok" }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder(/When I say.*start my day/).fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").first()).toBeVisible();

    await page.getByRole("button", { name: /Save Command/i }).click();
    await expect(page.getByText("Confirm Command Creation")).toBeVisible();

    // Click Confirm Save
    await page.getByRole("button", { name: /Confirm Save/i }).click();

    // Modal should close
    await expect(page.getByText("Confirm Command Creation")).not.toBeVisible();

    // Form should be reset - the generated command preview should be gone
    await expect(page.getByText("Generated Command")).not.toBeVisible();

    expect(putCalled).toBe(true);
  });

  test("save from manual mode calls PUT /api/v1/config", async ({ page }) => {
    let putCalled = false;

    await page.route("**/api/v1/config", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_CONFIG),
        });
      } else if (route.request().method() === "PUT") {
        putCalled = true;
        const body = JSON.parse(route.request().postData() || "{}");
        expect(body.commands).toHaveProperty("my_shell_cmd");
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok" }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Fill required fields
    await page.getByPlaceholder("my_command").fill("my_shell_cmd");
    await page.getByPlaceholder("My Command").fill("My Shell Command");
    await page.getByPlaceholder("Trigger phrase").fill("run shell");

    // Add a shell action with content
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.locator("select").first().selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("ls -la");

    // Save
    await page.getByRole("button", { name: /Save Command/i }).click();
    await expect(page.getByText("Confirm Command Creation")).toBeVisible();

    await page.getByRole("button", { name: /Confirm Save/i }).click();
    await expect(page.getByText("Confirm Command Creation")).not.toBeVisible();

    expect(putCalled).toBe(true);
  });
});

test.describe("Command Authoring - Validation Errors", () => {
  test("save with empty command name shows error", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Leave name empty, fill display name
    await page.getByPlaceholder("My Command").fill("Test");

    // Add an action so the "no actions" validation doesn't fire first
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.getByPlaceholder("e.g., ctrl+alt+t").fill("ctrl+c");

    await page.getByRole("button", { name: /Save Command/i }).click();

    // Error alert should appear
    await expect(page.getByText("Command name is required")).toBeVisible();

    // Modal should NOT appear
    await expect(page.getByText("Confirm Command Creation")).not.toBeVisible();
  });

  test("save with no actions shows error", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Fill name and display name but no actions
    await page.getByPlaceholder("my_command").fill("test_cmd");
    await page.getByPlaceholder("My Command").fill("Test Command");

    // The Save Command button should be disabled when there are no actions
    const saveBtn = page.getByRole("button", { name: /Save Command/i });
    await expect(saveBtn).toBeDisabled();
  });

  test("save with empty display name shows error", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Fill name but leave display name empty
    await page.getByPlaceholder("my_command").fill("test_cmd");

    // Add an action
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.getByPlaceholder("e.g., ctrl+alt+t").fill("ctrl+c");

    await page.getByRole("button", { name: /Save Command/i }).click();

    await expect(page.getByText("Display name is required")).toBeVisible();
  });

  test("save with action missing required field shows error", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    await page.getByPlaceholder("my_command").fill("test_cmd");
    await page.getByPlaceholder("My Command").fill("Test Command");

    // Add a keypress action but leave keys empty
    await page.getByRole("button", { name: /Add Action/i }).click();

    await page.getByRole("button", { name: /Save Command/i }).click();

    await expect(page.getByText(/Action 1 \(Keypress\) requires a 'keys' value/)).toBeVisible();
  });

  test("error alert can be dismissed", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    await page.getByPlaceholder("My Command").fill("Test");

    // Add an action to pass action check, trigger name error
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.getByPlaceholder("e.g., ctrl+alt+t").fill("ctrl+c");

    await page.getByRole("button", { name: /Save Command/i }).click();
    await expect(page.getByText("Command name is required")).toBeVisible();

    // Dismiss the error
    await page.getByRole("button", { name: "Close alert" }).click();
    await expect(page.getByText("Command name is required")).not.toBeVisible();
  });
});

test.describe("Command Authoring - AI Error Handling", () => {
  test("API error during generation shows error alert", async ({ page }) => {
    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder(/When I say.*start my day/).fill("open my browser");
    await page.getByRole("button", { name: /Generate Command/i }).click();

    // Error alert should appear
    await expect(page.getByText("Internal server error")).toBeVisible();

    // No preview should be shown
    await expect(page.getByText("Generated Command")).not.toBeVisible();
  });

  test("LLM-related error shows unavailable warning with Switch to Manual button", async ({
    page,
  }) => {
    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "LLM service is not configured" }),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder(/When I say.*start my day/).fill("open my browser");
    await page.getByRole("button", { name: /Generate Command/i }).click();

    // The error alert with the LLM message should appear
    await expect(page.getByText("LLM service is not configured")).toBeVisible();

    // The special "AI generation unavailable" warning should appear
    await expect(page.getByText("AI generation is currently unavailable")).toBeVisible();

    // "Switch to Manual" button should be present
    const switchBtn = page.getByRole("button", { name: /Switch to Manual/i });
    await expect(switchBtn).toBeVisible();

    // Clicking it should switch to manual mode
    await switchBtn.click();
    await expect(page.getByRole("tab", { name: /Manual Mode/i })).toHaveAttribute(
      "aria-selected",
      "true"
    );
    await expect(page.getByText("Manual Command Editor")).toBeVisible();
  });

  test("non-LLM error does not show unavailable warning", async ({ page }) => {
    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Description too short" }),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder(/When I say.*start my day/).fill("x");
    await page.getByRole("button", { name: /Generate Command/i }).click();

    // Generic error should show
    await expect(page.getByText("Description too short")).toBeVisible();

    // The LLM-specific warning should NOT appear
    await expect(page.getByText("AI generation is currently unavailable")).not.toBeVisible();
  });
});
