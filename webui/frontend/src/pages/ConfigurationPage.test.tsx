import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import ConfigurationPage from "./ConfigurationPage";
import { ThemeProvider } from "../components/ThemeProvider";
import { ToastProvider } from "../components/ToastProvider";
import { playTestTone, runMicTest } from "../utils/audioTest";
import { deleteVoiceModel, fetchVoiceModels } from "../services/api";

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
const fetchVoiceModelsMock = vi.mocked(fetchVoiceModels);
const deleteVoiceModelMock = vi.mocked(deleteVoiceModel);

const jsonResponse = (data: unknown, ok = true, status = 200) => ({
  ok,
  status,
  json: async () => data,
  text: async () => JSON.stringify(data),
});

beforeEach(() => {
  vi.clearAllMocks();
  fetchVoiceModelsMock.mockResolvedValue([]);
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
        <ToastProvider>
          <ConfigurationPage />
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
};

/** Switch to a named tab (the page is now organised into tabs). */
const goToTab = (name: RegExp) => {
  fireEvent.click(screen.getByRole("tab", { name }));
};

describe("ConfigurationPage audio device tests", () => {
  // Renders the page, waits for the config to load, then opens the Audio tab
  // so the device cards are present.
  const renderAudioTab = async () => {
    renderPage();
    await screen.findByRole("tab", { name: /Audio/ });
    goToTab(/Audio/);
  };

  test("mic/output test buttons are enabled without a server-side device selection", async () => {
    await renderAudioTab();
    // The browser test uses the browser's default devices, so it must not
    // depend on the (server-side) device dropdowns having a value.
    expect(screen.getByTestId("mic-test-button")).toBeEnabled();
    expect(screen.getByTestId("output-test-button")).toBeEnabled();
  });

  test("audio device selects expose accessible labels", async () => {
    await renderAudioTab();
    expect(screen.getByLabelText("Audio input device")).toBeInTheDocument();
    expect(screen.getByLabelText("Audio output device")).toBeInTheDocument();
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

    await renderAudioTab();
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
    await renderAudioTab();

    fireEvent.click(screen.getByTestId("mic-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("mic-test-result")).toHaveTextContent(
        "No signal detected — check your microphone",
      ),
    );
  });

  test("mic test surfaces permission errors instead of pretending success", async () => {
    runMicTestMock.mockRejectedValue(new Error("Permission denied"));
    await renderAudioTab();

    fireEvent.click(screen.getByTestId("mic-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("mic-test-result")).toHaveTextContent("Permission denied"),
    );
    expect(screen.getByTestId("mic-test-button")).toBeEnabled(); // retry allowed
  });

  test("mic test falls back to a generic message for empty errors", async () => {
    runMicTestMock.mockRejectedValue(new Error(""));
    await renderAudioTab();

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

    await renderAudioTab();
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
    await renderAudioTab();

    fireEvent.click(screen.getByTestId("output-test-button"));

    await waitFor(() =>
      expect(screen.getByTestId("output-test-status")).toHaveTextContent(
        "Web Audio is not supported in this browser.",
      ),
    );
    expect(screen.getByTestId("output-test-button")).toBeEnabled();
  });
});

describe("ConfigurationPage dirty-state + save", () => {
  test("Save is disabled and labelled 'Saved' when the config is clean", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("save-button")).toBeDisabled();
    });
    expect(screen.getByTestId("save-button")).toHaveTextContent("Saved");
    expect(screen.getByTestId("discard-button")).toBeDisabled();
    expect(screen.getByTestId("dirty-status")).toHaveTextContent("All changes saved");
  });

  test("editing a field marks the form dirty and enables Save", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId("save-button")).toBeDisabled());

    // Theme select lives on the (default) General tab.
    fireEvent.change(screen.getByLabelText("Theme"), { target: { value: "light" } });

    expect(screen.getByTestId("save-button")).toBeEnabled();
    expect(screen.getByTestId("save-button")).toHaveTextContent("Save Changes");
    expect(screen.getByTestId("dirty-status")).toHaveTextContent("Unsaved changes");
  });

  test("Discard reverts changes back to the loaded config", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId("save-button")).toBeDisabled());

    const themeSelect = screen.getByLabelText("Theme") as HTMLSelectElement;
    fireEvent.change(themeSelect, { target: { value: "light" } });
    expect(themeSelect.value).toBe("light");

    fireEvent.click(screen.getByTestId("discard-button"));

    expect(themeSelect.value).toBe("dark");
    expect(screen.getByTestId("save-button")).toBeDisabled();
  });

  test("a failed save (res not ok) surfaces the real error via a toast", async () => {
    global.fetch = vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/v1/audio/devices")) {
        return jsonResponse({ input: [], output: [] });
      }
      if (url.includes("/api/v1/config") && init?.method === "PUT") {
        return jsonResponse({ detail: "Disallowed config keys: advisors" }, false, 422);
      }
      if (url.includes("/api/v1/config")) {
        return jsonResponse({});
      }
      return jsonResponse({});
    }) as unknown as typeof fetch;

    renderPage();
    await waitFor(() => expect(screen.getByTestId("save-button")).toBeDisabled());

    fireEvent.change(screen.getByLabelText("Theme"), { target: { value: "light" } });
    fireEvent.click(screen.getByTestId("save-button"));

    await screen.findByText(/Failed to save configuration: Disallowed config keys: advisors/);
    // Still dirty after a failed save.
    expect(screen.getByTestId("save-button")).toBeEnabled();
  });

  test("a successful save shows a success toast and clears the dirty flag", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId("save-button")).toBeDisabled());

    fireEvent.change(screen.getByLabelText("Theme"), { target: { value: "light" } });
    fireEvent.click(screen.getByTestId("save-button"));

    await screen.findByText("Configuration saved successfully.");
    await waitFor(() => expect(screen.getByTestId("save-button")).toBeDisabled());
  });
});

describe("ConfigurationPage voice-model delete confirmation", () => {
  test("clicking the trash icon asks for confirmation before deleting", async () => {
    fetchVoiceModelsMock.mockResolvedValue([
      {
        name: "hey_jarvis.onnx",
        path: "/models/hey_jarvis.onnx",
        size_bytes: 1024,
        size_human: "1 KB",
        modified: "2026-01-01",
        state: "idle",
      },
    ]);

    renderPage();
    await screen.findByRole("tab", { name: /Voice Models/ });
    goToTab(/Voice Models/);

    fireEvent.click(await screen.findByLabelText("Delete model hey_jarvis.onnx"));

    // A confirmation dialog appears; nothing was deleted yet.
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("Delete voice model?");
    expect(deleteVoiceModelMock).not.toHaveBeenCalled();

    // Cancel leaves the model intact.
    fireEvent.click(screen.getByTestId("delete-cancel"));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(deleteVoiceModelMock).not.toHaveBeenCalled();
  });

  test("confirming the dialog deletes the model", async () => {
    deleteVoiceModelMock.mockResolvedValue(undefined);
    fetchVoiceModelsMock.mockResolvedValue([
      {
        name: "hey_jarvis.onnx",
        path: "/models/hey_jarvis.onnx",
        size_bytes: 1024,
        size_human: "1 KB",
        modified: "2026-01-01",
        state: "idle",
      },
    ]);

    renderPage();
    await screen.findByRole("tab", { name: /Voice Models/ });
    goToTab(/Voice Models/);

    fireEvent.click(await screen.findByLabelText("Delete model hey_jarvis.onnx"));
    await screen.findByRole("dialog");
    fireEvent.click(screen.getByTestId("delete-confirm"));

    // React Query passes a context object as the 2nd arg, so assert on the 1st.
    await waitFor(() => expect(deleteVoiceModelMock).toHaveBeenCalled());
    expect(deleteVoiceModelMock.mock.calls[0][0]).toBe("hey_jarvis.onnx");
  });
});
