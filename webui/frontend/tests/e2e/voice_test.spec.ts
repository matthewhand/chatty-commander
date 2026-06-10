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

    const banner = page.getByTestId("dry-run-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toContainText(
      "Dry-run mode: detected commands are reported, not executed."
    );

    // The page connects to the live /ws/voice-test endpoint on load and
    // sends the {type: "start", dry_run: true} handshake; the backend
    // acknowledges with a "listening" stage event confirming dry-run mode.
    await waitForWsConnected(page);
    const listeningEvent = page.locator(
      '[data-testid="voice-stage-event"][data-stage="listening"]'
    );
    await expect(listeningEvent).toHaveCount(1, { timeout: 10_000 });
    await expect(listeningEvent).toContainText("dry_run: true");
    await expect(listeningEvent).toHaveAttribute("data-status", "success");
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

    const micToggle = page.getByTestId("mic-toggle");
    await expect(micToggle).toHaveText(/Enable microphone/);
    await micToggle.click();

    // Fake media stream: permission is auto-granted, no prompt, so the page
    // must land in the "active" state (not "denied").
    await expect(page.getByTestId("mic-state")).toHaveText(
      /Listening — audio is streaming to the server/,
      { timeout: 10_000 }
    );
    await expect(page.getByTestId("mic-denied-alert")).toHaveCount(0);
    await expect(micToggle).toHaveText(/Stop microphone/);

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
  });
});
