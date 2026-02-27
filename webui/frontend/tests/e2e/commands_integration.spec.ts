import { test, expect } from '@playwright/test';

test('Commands page should render commands from backend API', async ({ page }) => {
  // Mock the /api/v1/config endpoint
  await page.route('**/api/v1/config', async route => {
    const json = {
      commands: {
        repro_command_123: {
          action: "keypress",
          keys: "f",
          message: null,
          url: null
        },
        another_command: {
           action: "custom_message",
           message: "Hello World",
           keys: null,
           url: null
        }
      },
      // Mock other necessary config parts to avoid crashes if any
      state_models: {},
      wake_words: ["hey_jarvis", "computer"]
    };
    await route.fulfill({ json });
  });

  // Mock other endpoints that might be called on load to prevent errors
  await page.route('**/api/v1/status', async route => {
      await route.fulfill({ json: { status: 'ok', version: '0.0.0' } });
  });
  await page.route('**/api/v1/state', async route => {
      await route.fulfill({ json: { current_state: 'idle' } });
  });

  // Navigate to the commands page
  // Note: We might need to bypass login or mock auth state if the app requires it.
  // Assuming for now we can access it or the test setup handles it.
  // If useAuth hook blocks this, we might need to mock the auth response too.
  await page.goto('/commands');

  // Check if the specific command ID or display name from our mock is visible
  // The current implementation uses the key as the display name if not specified otherwise,
  // or we might need to adjust based on how the transformation logic will work.
  // For the reproduction, we expect "repro_command_123" to be NOT visible initially (failure case),
  // and visible after the fix.

  await expect(page.getByText('repro_command_123')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('another_command')).toBeVisible();

  // Verify wakewords are displayed (restored functionality)
  // Since we map global wakewords to ALL commands, "Hey Jarvis" should appear multiple times (once per command)
  // We check that the first instance is visible, confirming the mapping logic is working.
  await expect(page.getByText('Hey Jarvis').first()).toBeVisible();
});
