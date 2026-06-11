import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import ConfigurationPage from "./ConfigurationPage";
import { ThemeProvider } from "../components/ThemeProvider";
import { playTestTone, runMicTest } from "../utils/audioTest";

vi.mock("../services/api", () => ({
  fetchLLMModels: vi.fn().mockResolvedValue([]),
  fetchVoiceModels: vi.fn().mockResolvedValue([]),
  uploadVoiceModel: vi.fn(),
  deleteVoiceModel: vi.fn(),
}));

// The in-browser audio tests are unit-tested in utils/audioTest.test.ts;
// here we only verify the page wires them up and renders honest feedback.
vi.mock("../utils/audioTest", () => ({
  runMicTest: vi.fn(),
  playTestTone: vi.fn(),
}));

const runMicTestMock = vi.mocked(runMicTest);
const playTestToneMock = vi.mocked(playTestTone);

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  json: async () => data,
});

beforeEach(() => {
  vi.clearAllMocks();
  global.fetch = vi.fn(async (input: unknown) => {
    const url = String(input);
    if (url.includes("/api/v1/audio/devices")) {
      return jsonResponse({ input: ["Built-in Mic"], output: ["Built-in Speakers"] });
    }
    if (url.includes("/api/v1/config")) {
      return jsonResponse({});
    }
    return jsonResponse({});
  }) as unknown as typeof fetch;
});

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ConfigurationPage />
      </ThemeProvider>
    </QueryClientProvider>,
  );
};

describe("ConfigurationPage audio device tests", () => {
  test("test buttons are enabled without a server-side device selection", () => {
    renderPage();
    // The browser test uses the browser's default devices, so it must not
    // depend on the (server-side) device dropdowns having a value.
    expect(screen.getByTestId("mic-test-button")).toBeEnabled();
    expect(screen.getByTestId("output-test-button")).toBeEnabled();
  });

  test("mic test shows a live level meter and reports the detected peak", async () => {
    let capturedOpts: Parameters<typeof runMicTest>[0];
    let resolveMic!: (r: { peakLevel: number }) => void;
    runMicTestMock.mockImplementation((opts) => {
      capturedOpts = opts;
      return new Promise((resolve) => {
        resolveMic = resolve;
      });
    });

    renderPage();
    fireEvent.click(screen.getByTestId("mic-test-button"));

    // While testing: button disabled, real meter rendered.
    expect(screen.getByTestId("mic-test-button")).toBeDisabled();
    expect(screen.getByTestId("mic-test-button")).toHaveTextContent("Testing...");
    const meter = screen.getByRole("meter", { name: "Microphone input level" });
    expect(meter).toHaveAttribute("aria-valuenow", "0");

    // Live levels from the analyser drive the meter.
    act(() => capturedOpts!.onLevel!(42));
    expect(screen.getByTestId("mic-test-meter")).toHaveAttribute("aria-valuenow", "42");

    await act(async () => resolveMic({ peakLevel: 42 }));

    expect(screen.getByTestId("mic-test-result")).toHaveTextContent("Signal detected (peak 42%)");
    expect(screen.queryByTestId("mic-test-meter")).not.toBeInTheDocument();
    expect(screen.getByTestId("mic-test-button")).toBeEnabled();
    expect(runMicTestMock).toHaveBeenCalledTimes(1);
  });

  test("mic test reports no signal when the peak is below the threshold", async () => {
    runMicTestMock.mockResolvedValue({ peakLevel: 0 });
    renderPage();

    fireEvent.click(screen.getByTestId("mic-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("mic-test-result")).toHaveTextContent(
        "No signal detected — check your microphone",
      ),
    );
  });

  test("mic test surfaces permission errors instead of pretending success", async () => {
    runMicTestMock.mockRejectedValue(new Error("Permission denied"));
    renderPage();

    fireEvent.click(screen.getByTestId("mic-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("mic-test-result")).toHaveTextContent("Permission denied"),
    );
    expect(screen.getByTestId("mic-test-button")).toBeEnabled(); // retry allowed
  });

  test("mic test falls back to a generic message for empty errors", async () => {
    runMicTestMock.mockRejectedValue(new Error(""));
    renderPage();

    fireEvent.click(screen.getByTestId("mic-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("mic-test-result")).toHaveTextContent(
        "Microphone access was denied or is unavailable.",
      ),
    );
  });

  test("output test plays a real tone and reports completion", async () => {
    let resolveTone!: () => void;
    playTestToneMock.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveTone = resolve;
        }),
    );

    renderPage();
    fireEvent.click(screen.getByTestId("output-test-button"));

    expect(screen.getByTestId("output-test-button")).toBeDisabled();
    expect(screen.getByTestId("output-test-button")).toHaveTextContent("Playing...");
    expect(screen.getByTestId("output-test-status")).toHaveTextContent(
      "Playing 440 Hz test tone...",
    );

    await act(async () => resolveTone());

    expect(screen.getByTestId("output-test-status")).toHaveTextContent("Test tone played");
    expect(screen.getByTestId("output-test-button")).toBeEnabled();
    expect(playTestToneMock).toHaveBeenCalledTimes(1);
  });

  test("output test surfaces Web Audio failures", async () => {
    playTestToneMock.mockRejectedValue(new Error("Web Audio is not supported in this browser."));
    renderPage();

    fireEvent.click(screen.getByTestId("output-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("output-test-status")).toHaveTextContent(
        "Web Audio is not supported in this browser.",
      ),
    );
    expect(screen.getByTestId("output-test-button")).toBeEnabled();
  });
});
