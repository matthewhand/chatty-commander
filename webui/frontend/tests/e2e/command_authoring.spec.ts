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
      name: "Take Screenshot",
      actions: [{ type: "shell", cmd: "gnome-screenshot" }],
    },
  },
  settings: {},
};

/**
 * Set up route mocks that most tests need: the GET /api/v1/config endpoint
 * (read on mount to learn existing command names, and again during save) and
 * the PUT used when persisting. The page reads existing names from this config
 * to block silent name collisions, so MOCK_CONFIG is the source of truth for
 * "which names already exist".
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

/**
 * Convenience accessor for the save-confirmation modal. The page now renders a
 * real role="dialog" (focus-trapped, Escape-closable), and there are *also*
 * page-level "Cancel" buttons in both AI and Manual mode, so modal buttons MUST
 * be scoped to the dialog to avoid strict-mode ambiguity.
 */
function confirmDialog(page: import("@playwright/test").Page) {
  return page.getByRole("dialog");
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

    const textarea = page.getByPlaceholder("When I say 'start my day'");
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

    const textarea = page.getByPlaceholder("When I say 'start my day'");
    await textarea.fill("start my day workflow");

    await page.getByRole("button", { name: /Generate Command/i }).click();

    // Verify generated command preview shows all fields
    // modern Playwright: getByRole heading instead of getByText(...).first() (scoped, avoids brittle)
    await expect(page.getByRole("heading", { name: "Generated Command" })).toBeVisible();
    await expect(page.getByText("start_my_day")).toBeVisible();
    await expect(page.getByText("Start My Day", { exact: true })).toBeVisible();
    await expect(page.getByText("start my day", { exact: true })).toBeVisible();

    // Verify actions are shown
    await expect(page.getByText("code ~/projects")).toBeVisible();
    await expect(page.getByText("https://mail.google.com")).toBeVisible();
    await expect(page.getByText("ctrl+alt+t")).toBeVisible();

    // Verify action type badges (use .nth(0) scoped instead of brittle .first(); modern PW best practice)
    await expect(page.getByText("shell").nth(0)).toBeVisible();
    await expect(page.getByText("url").nth(0)).toBeVisible();
    await expect(page.getByText("keypress").nth(0)).toBeVisible();
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

    const textarea = page.getByPlaceholder("When I say 'start my day'");
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

    const textarea = page.getByPlaceholder("When I say 'start my day'");
    await textarea.fill("start my day workflow");

    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByRole("heading", { name: "Generated Command" })).toBeVisible();

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
    // Default type should be keypress. The app shell exposes a global theme
    // <select>, so the first page select isn't the action type — target the
    // per-action type select by its stable id (#action-type-<index>).
    const typeSelect = page.locator("#action-type-0");
    await expect(typeSelect).toHaveValue("keypress");
  });

  test("can select different action types and fill type-specific fields", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Add action and select URL type
    await page.getByRole("button", { name: /Add Action/i }).click();
    // Target the per-action type select by id (the shell's theme select is the
    // first <select> on the page).
    const typeSelect = page.locator("#action-type-0");
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
    await removeButtons.nth(0).click();

    // Only one action should remain
    await expect(page.getByText("Action 1")).toBeVisible();
    await expect(page.getByText("Action 2")).not.toBeVisible();
  });

  test("adding multiple actions of different types works correctly", async ({ page }) => {
    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // Add a shell action
    await page.getByRole("button", { name: /Add Action/i }).click();
    const firstSelect = page.locator("#action-type-0");
    await firstSelect.selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("echo hello");

    // Add a URL action
    await page.getByRole("button", { name: /Add Action/i }).click();
    const secondSelect = page.locator("#action-type-1");
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
    await page.getByPlaceholder("When I say 'start my day'").fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").nth(0)).toBeVisible();

    // Click Save Command
    await page.getByRole("button", { name: /Save Command/i }).click();

    // Confirmation modal should appear as a real dialog with the create heading.
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByRole("heading", { name: "Confirm Command Creation" })
    ).toBeVisible();

    // Command summary should be in the modal (scope to the dialog so we don't
    // match the same text in the preview card behind it).
    await expect(dialog.getByText("start_my_day")).toBeVisible();
    // exact:true — "Start My Day" matches the wakeword "start my day"
    // case-insensitively otherwise.
    await expect(dialog.getByText("Start My Day", { exact: true })).toBeVisible();

    // Actions count should be shown
    await expect(dialog.getByText(/Actions \(3\)/)).toBeVisible();
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

    await page.getByPlaceholder("When I say 'start my day'").fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByText("Generated Command").nth(0)).toBeVisible();

    await page.getByRole("button", { name: /Save Command/i }).click();
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();

    // Click Cancel inside the dialog (a page-level Cancel button also exists, so
    // we scope to the dialog to disambiguate).
    await dialog.getByRole("button", { name: /^Cancel$/ }).click();

    // Modal should be dismissed and we should NOT have navigated away.
    await expect(confirmDialog(page)).toHaveCount(0);
    await expect(page).toHaveURL(/\/commands\/authoring/);

    // The generated command preview should still be visible
    await expect(page.getByRole("heading", { name: "Generated Command" })).toBeVisible();
  });

  test("Escape key closes the confirmation modal", async ({ page }) => {
    await setupBaseMocks(page);

    await page.route("**/api/v1/commands/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_GENERATED_COMMAND),
      });
    });

    await page.goto("/commands/authoring");

    await page.getByPlaceholder("When I say 'start my day'").fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByRole("heading", { name: "Generated Command" })).toBeVisible();

    await page.getByRole("button", { name: /Save Command/i }).click();
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();

    // The dialog focuses Cancel on open; pressing Escape closes it.
    await expect(dialog.getByRole("button", { name: /^Cancel$/ })).toBeFocused();
    await page.keyboard.press("Escape");

    await expect(confirmDialog(page)).toHaveCount(0);
    // Escape is a dismiss, not a save: stay on the authoring page.
    await expect(page).toHaveURL(/\/commands\/authoring/);
  });

  test("Confirm Save persists via PUT, toasts success, and navigates to /commands", async ({ page }) => {
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

    await page.getByPlaceholder("When I say 'start my day'").fill("start my day");
    await page.getByRole("button", { name: /Generate Command/i }).click();
    await expect(page.getByRole("heading", { name: "Generated Command" })).toBeVisible();

    await page.getByRole("button", { name: /Save Command/i }).click();
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();

    // Click Confirm Save (scoped to the dialog)
    await dialog.getByRole("button", { name: /Confirm Save/i }).click();

    // A success toast should announce the creation.
    await expect(
      page.getByText('Command "start_my_day" created.')
    ).toBeVisible();

    // On success the page no longer resets in place — it navigates to the
    // command list, where the Commands page heading is shown.
    await expect(page).toHaveURL(/\/commands(\?.*)?$/);
    await expect(
      page.getByRole("heading", { name: "Commands & Triggers" })
    ).toBeVisible();

    // And the authoring confirm modal is gone. (The destination /commands page
    // mounts its own native <dialog> elements, so assert the authoring dialog
    // specifically by its title rather than "no dialog at all".)
    await expect(
      page.getByRole("heading", { name: "Confirm Command Creation" })
    ).toHaveCount(0);

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
    await page.locator("#action-type-0").selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("ls -la");

    // Save
    await page.getByRole("button", { name: /Save Command/i }).click();
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();

    await dialog.getByRole("button", { name: /Confirm Save/i }).click();

    // Successful save navigates to the command list (no in-place reset). The
    // /commands page has its own native <dialog>s, so assert the authoring
    // confirm dialog specifically (by title) rather than "no dialog at all".
    await expect(page).toHaveURL(/\/commands(\?.*)?$/);
    await expect(
      page.getByRole("heading", { name: "Confirm Command Creation" })
    ).toHaveCount(0);

    expect(putCalled).toBe(true);
  });

  test("page-level Cancel button returns to /commands without saving", async ({ page }) => {
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
        await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
      } else {
        await route.continue();
      }
    });

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // The page-level Cancel (a ghost button beside Save Command) abandons the
    // editor and returns to the command list.
    await page.getByRole("button", { name: /^Cancel$/ }).click();

    await expect(page).toHaveURL(/\/commands(\?.*)?$/);
    await expect(
      page.getByRole("heading", { name: "Commands & Triggers" })
    ).toBeVisible();
    expect(putCalled).toBe(false);
  });

  test("blocks saving a command whose name already exists", async ({ page }) => {
    await setupBaseMocks(page);

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    // "take_screenshot" already exists in MOCK_CONFIG — reusing it must be
    // blocked (no ?edit= override present) rather than silently clobbering it.
    await page.getByPlaceholder("my_command").fill("take_screenshot");
    await page.getByPlaceholder("My Command").fill("Take Screenshot");
    await page.getByPlaceholder("Trigger phrase").fill("screenshot");
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.getByPlaceholder("e.g., ctrl+alt+t").fill("ctrl+c");

    await page.getByRole("button", { name: /Save Command/i }).click();

    // A blocking error is shown and the confirm dialog never opens.
    await expect(page.getByText(/already exists/i)).toBeVisible();
    await expect(confirmDialog(page)).toHaveCount(0);
  });

  test("editing via ?edit= allows saving the existing name", async ({ page }) => {
    await setupBaseMocks(page);

    // Arrive in edit mode for an existing command; saving its own name must NOT
    // be treated as a collision.
    await page.goto("/commands/authoring?edit=take_screenshot");

    // Edit mode preloads the manual editor with the existing definition.
    await expect(page.getByPlaceholder("my_command")).toHaveValue("take_screenshot");

    await page.getByRole("button", { name: /Save Command/i }).click();

    // No collision error; the confirm dialog (in "changes" wording) opens.
    await expect(page.getByText(/already exists/i)).toHaveCount(0);
    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByRole("heading", { name: "Confirm Command Changes" })
    ).toBeVisible();
  });
});

test.describe("Command Authoring - Danger Warnings", () => {
  test("inline warning is shown for a destructive rm -rf shell command", async ({ page }) => {
    await setupBaseMocks(page);

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.locator("#action-type-0").selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("rm -rf /tmp/x");

    // The per-action danger heuristic surfaces an inline advisory warning.
    await expect(page.getByText(/recursive\/forced delete|permanently destroy/i)).toBeVisible();
  });

  test("inline warning is shown for an insecure non-local http:// URL", async ({ page }) => {
    await setupBaseMocks(page);

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.locator("#action-type-0").selectOption("url");
    await page.getByPlaceholder("https://example.com").fill("http://example.com");

    await expect(page.getByText(/insecure http/i)).toBeVisible();
  });

  test("risky actions are flagged prominently in the confirm dialog", async ({ page }) => {
    await setupBaseMocks(page);

    await page.goto("/commands/authoring");
    await page.getByRole("tab", { name: /Manual Mode/i }).click();

    await page.getByPlaceholder("my_command").fill("risky_cmd");
    await page.getByPlaceholder("My Command").fill("Risky Command");
    await page.getByPlaceholder("Trigger phrase").fill("do risky thing");
    await page.getByRole("button", { name: /Add Action/i }).click();
    await page.locator("#action-type-0").selectOption("shell");
    await page.getByPlaceholder("e.g., npm start").fill("sudo rm -rf /tmp/x");

    await page.getByRole("button", { name: /Save Command/i }).click();

    const dialog = confirmDialog(page);
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/Potentially risky actions flagged/i)).toBeVisible();
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

    // The confirm dialog should NOT open on a validation failure.
    await expect(confirmDialog(page)).toHaveCount(0);
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

    // Add a keypress action but leave keys empty. The empty action shows an
    // inline per-action validation error immediately.
    await page.getByRole("button", { name: /Add Action/i }).click();

    await expect(
      page.getByText(/Keypress requires a 'keys' value/)
    ).toBeVisible();

    // The Save button stays enabled (action-level errors aren't part of the
    // field-error gating), but attempting to save surfaces a blocking
    // page-level "Action N: ..." error and never opens the confirm dialog.
    const saveBtn = page.getByRole("button", { name: /Save Command/i });
    await expect(saveBtn).toBeEnabled();
    await saveBtn.click();

    await expect(
      page.getByText(/Action 1: Keypress requires a 'keys' value/)
    ).toBeVisible();
    await expect(confirmDialog(page)).toHaveCount(0);
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
    await page.getByRole("button", { name: "Dismiss error" }).click();
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

    await page.getByPlaceholder("When I say 'start my day'").fill("open my browser");
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

    await page.getByPlaceholder("When I say 'start my day'").fill("open my browser");
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

    await page.getByPlaceholder("When I say 'start my day'").fill("x");
    await page.getByRole("button", { name: /Generate Command/i }).click();

    // Generic error should show
    await expect(page.getByText("Description too short")).toBeVisible();

    // The LLM-specific warning should NOT appear
    await expect(page.getByText("AI generation is currently unavailable")).not.toBeVisible();
  });
});
