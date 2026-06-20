import { test as base, expect, chromium, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Voice Test page (in-browser voice testing, dry-run pipeline)
//
// Runs against the real test backend started by playwright.config.ts
// (`--web --test-mode --no-auth` on port 8100), which serves the built SPA
// and the /ws/voice-test WebSocket endpoint. Nothing is mocked: the
// transcript -> match -> action events come from the live dry-run pipeline
// (VoiceTestPipeline) matching against the repo-root config.json commands.
//
// Microphone access uses Chromium's fake media stream so no permission
// prompt or real audio hardware is needed:
//   --use-fake-ui-for-media-stream     auto-accepts getUserMedia
//   --use-fake-device-for-media-stream provides a synthetic audio input
//
// The flags are browser-launch arguments, and `test.use({ launchOptions })`
// does not reliably re-launch the worker's shared browser with extra args,
// so the mic tests launch their own Chromium via an explicit fixture.
//
// The backend's SecurityHeadersMiddleware serves
// `Permissions-Policy: microphone=(self)`, which permits same-origin
// getUserMedia — asserted below so a regression to `microphone=()` (which
// blocks the mic in every real browser) is caught here.
// ---------------------------------------------------------------------------

const test = base.extend<{ fakeMicPage: Page }>({
  fakeMicPage: async ({ baseURL }, use) => {
    const browser = await chromium.launch({
      args: [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
      ],
    });
    const context = await browser.newContext({
      baseURL,
      permissions: ["microphone"],
    });
    const page = await context.newPage();
    await use(page);
    await browser.close();
  },
});

// A command present in the backend's test-mode config (config.json ->
// model_actions). "lights on" whole-word matches the "lights_on" command,
// whose action is a URL, so the dry-run description is "would open <url>".
const SIMULATED_UTTERANCE = "lights on";
const EXPECTED_COMMAND = "lights_on";

async function gotoVoiceTest(page: Page) {
  await page.goto("/voice-test");
  await expect(page.getByTestId("voice-test-page")).toBeVisible();
}

/** The simulate-send button is disabled until the WebSocket is connected. */
async function waitForWsConnected(page: Page) {
  await expect(page.getByTestId("voice-ws-status")).toHaveText(/Connected/, {
    timeout: 15_000,
  });
}

test.describe("Voice Test page", () => {
  test("loads with the dry-run banner and connects its WebSocket", async ({
    page,
  }) => {
    await gotoVoiceTest(page);

    // Subtitle under the H1 sets honest expectations (no real actions run).
    await expect(page.getByRole("heading", { name: "Voice Test" })).toBeVisible();
    await expect(page.getByTestId("voice-test-subtitle")).toContainText(
      /no real actions run/i
    );

    const banner = page.getByTestId("dry-run-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toContainText("What to expect:");
    await expect(banner).toContainText(
      "dry-run mode — detected commands are reported, not executed."
    );

    // The verify-setup checklist starts with the server-connected row pending
    // and ticks once the WebSocket is up (asserted after waitForWsConnected).
    const checklist = page.getByTestId("voice-checklist");
    await expect(checklist).toBeVisible();
    await expect(checklist).toContainText("Verify setup");
    await expect(checklist).toContainText("Wake word detected");

    // The example wake-word chips fill the simulation input.
    const chips = page.getByTestId("wake-word-chip");
    await expect(chips.first()).toBeVisible();
    const firstChipText = (await chips.first().textContent())?.trim() ?? "";
    await chips.first().click();
    await expect(page.getByTestId("voice-simulate-input")).toHaveValue(
      firstChipText
    );

    // The "Edit commands" cross-link points at the commands page.
    await expect(page.getByTestId("edit-commands-link")).toHaveAttribute(
      "href",
      "/commands"
    );

    // The page connects to the live /ws/voice-test endpoint on load and
    // sends the {type: "start", dry_run: true} handshake; the backend
    // acknowledges with a "listening" stage event confirming dry-run mode.
    await waitForWsConnected(page);

    // Once connected, the "Server connected" checklist row is ticked.
    await expect(
      checklist.locator('li[data-checked="true"]', { hasText: "Server connected" })
    ).toBeVisible();

    const listeningEvent = page.locator(
      '[data-testid="voice-stage-event"][data-stage="listening"]'
    );
    await expect(listeningEvent).toHaveCount(1, { timeout: 10_000 });
    await expect(listeningEvent).toContainText("dry_run: true");
    await expect(listeningEvent).toHaveAttribute("data-status", "success");

    // The timeline is an aria-live log so screen readers announce new stages.
    const timeline = page.getByTestId("voice-stage-timeline");
    await expect(timeline).toHaveAttribute("role", "log");
    await expect(timeline).toHaveAttribute("aria-live", "polite");
  });

  test("enabling the microphone reaches the active state and renders the level meter", async ({
    fakeMicPage: page,
  }) => {
    // The server must permit same-origin microphone access; a regression to
    // `microphone=()` blocks getUserMedia in every real browser.
    const response = await page.request.get("/voice-test");
    expect(response.headers()["permissions-policy"] ?? "").toContain(
      "microphone=(self)"
    );

    await gotoVoiceTest(page);

    // The microphone input-device picker is present and defaults to "System
    // default" before any device labels are known.
    const deviceSelect = page.getByTestId("voice-device-select");
    await expect(deviceSelect).toBeVisible();
    await expect(
      deviceSelect.getByRole("option", { name: "System default" })
    ).toBeAttached();

    const micToggle = page.getByTestId("mic-toggle");
    await expect(micToggle).toHaveText(/Enable microphone/);
    await micToggle.click();

    // Fake media stream: permission is auto-granted, no prompt, so the page
    // must land in the active state (not "denied"). Real Chromium provides
    // MediaRecorder, so the recorder runs and the WS is up — the honest
    // streaming wording is "Listening — streaming to server".
    await expect(page.getByTestId("mic-state")).toHaveText(
      /Listening — streaming to server/,
      { timeout: 10_000 }
    );
    await expect(page.getByTestId("mic-denied-alert")).toHaveCount(0);
    // When truly streaming, the "mic on but not streaming" warning is absent.
    await expect(page.getByTestId("mic-stream-warning")).toHaveCount(0);
    await expect(micToggle).toHaveText(/Stop microphone/);

    // The "Microphone active and streaming" checklist row ticks.
    await expect(
      page
        .getByTestId("voice-checklist")
        .locator('li[data-checked="true"]', {
          hasText: "Microphone active and streaming",
        })
    ).toBeVisible();

    // The input level meter renders as an accessible meter element.
    const meter = page.getByTestId("voice-level-meter");
    await expect(meter).toBeVisible();
    await expect(meter).toHaveRole("meter");
    await expect(meter).toHaveAttribute("aria-valuemin", "0");
    await expect(meter).toHaveAttribute("aria-valuemax", "100");

    // The fake audio device emits a periodic tone; the AnalyserNode loop must
    // report a non-zero level at some point. waitForFunction polls on rAF so
    // it can catch the level mid-beep.
    await page.waitForFunction(
      () => {
        const el = document.querySelector(
          '[data-testid="voice-level-meter"]'
        );
        return (
          el !== null && Number(el.getAttribute("aria-valuenow") ?? "0") > 0
        );
      },
      undefined,
      { timeout: 15_000 }
    );

    // Toggling again stops the mic and removes the meter.
    await micToggle.click();
    await expect(page.getByTestId("mic-state")).toHaveText(/Microphone off/);
    await expect(meter).toHaveCount(0);
  });

  test("simulated text command renders transcript -> match -> dry-run action", async ({
    page,
  }) => {
    await gotoVoiceTest(page);
    await waitForWsConnected(page);

    // Before any transcript arrives, the dedicated transcript panel shows a
    // placeholder. On the real test backend speech-to-text isn't configured, so
    // the panel reports "transcript-unavailable" rather than the generic
    // "transcript-empty"; accept either pre-transcript placeholder.
    await expect(page.getByTestId("voice-transcript-panel")).toBeVisible();
    await expect(
      page
        .getByTestId("transcript-empty")
        .or(page.getByTestId("transcript-unavailable")),
    ).toBeVisible();

    const input = page.getByTestId("voice-simulate-input");
    const send = page.getByTestId("voice-simulate-send");
    await input.fill(SIMULATED_UTTERANCE);
    await expect(send).toBeEnabled();
    await send.click();

    const timeline = page.getByTestId("voice-stage-timeline");
    await expect(timeline).toBeVisible({ timeout: 10_000 });
    const events = page.getByTestId("voice-stage-event");

    // Transcript stage echoes the simulated utterance.
    const transcriptEvent = page.locator(
      '[data-testid="voice-stage-event"][data-stage="transcript"]'
    );
    await expect(transcriptEvent).toHaveCount(1, { timeout: 10_000 });
    await expect(transcriptEvent).toContainText(SIMULATED_UTTERANCE);
    await expect(transcriptEvent).toContainText("simulated: true");
    await expect(transcriptEvent).toHaveAttribute("data-status", "success");

    // Match stage reports a successful match against the configured command.
    const matchEvent = page.locator(
      '[data-testid="voice-stage-event"][data-stage="match"]'
    );
    await expect(matchEvent).toHaveCount(1);
    await expect(matchEvent).toContainText("matched: true");
    await expect(matchEvent).toContainText(`command: ${EXPECTED_COMMAND}`);
    await expect(matchEvent).toHaveAttribute("data-status", "success");

    // Dry-run action stage: describes what WOULD run, executes nothing.
    const actionEvent = page.locator(
      '[data-testid="voice-stage-event"][data-stage="action"]'
    );
    await expect(actionEvent).toHaveCount(1);
    await expect(actionEvent).toContainText(`command: ${EXPECTED_COMMAND}`);
    await expect(actionEvent).toContainText("dry_run: true");
    await expect(actionEvent).toContainText("executed: false");
    await expect(actionEvent).toContainText(/would/);
    await expect(actionEvent).toHaveAttribute("data-status", "success");

    // Stages arrive in pipeline order: transcript before match before action.
    const stages = await events.evaluateAll((els) =>
      els.map((el) => el.getAttribute("data-stage"))
    );
    const ti = stages.indexOf("transcript");
    const mi = stages.indexOf("match");
    const ai = stages.indexOf("action");
    expect(ti).toBeGreaterThanOrEqual(0);
    expect(mi).toBeGreaterThan(ti);
    expect(ai).toBeGreaterThan(mi);

    // The recognized text (the simulated utterance) is surfaced to the user.
    // When server-side speech-to-text is configured the dedicated transcript
    // panel shows it; on the test backend STT is unavailable, so the panel
    // keeps its "unavailable" notice and the recognized text is surfaced via the
    // transcript stage event in the timeline instead. Accept whichever path
    // applies in the current environment.
    await expect(
      page
        .getByTestId("transcript-text")
        .or(
          page.locator(
            '[data-testid="voice-stage-event"][data-stage="transcript"]',
          ),
        )
        .filter({ hasText: SIMULATED_UTTERANCE }),
    ).toBeVisible();

    // A successful match ticks the "Command matched" checklist row.
    await expect(
      page
        .getByTestId("voice-checklist")
        .locator('li[data-checked="true"]', { hasText: "Command matched" })
    ).toBeVisible();

    // Small addition: 2 Playwright request asserts for wired endpoints used in voice/dry-run flow (commands for match, per WEBUI expand e2e)
    const cmdResp = await page.request.get("/api/v1/commands");
    expect(cmdResp.ok()).toBeTruthy();
    const cmdData = await cmdResp.json();
    expect(Array.isArray(cmdData) || (cmdData && typeof cmdData === "object")).toBe(true);
  });
});
