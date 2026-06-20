import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router-dom";
import { vi } from "vitest";
import ConfigurationPage from "./ConfigurationPage";
import { ThemeProvider, AVAILABLE_THEMES } from "../components/ThemeProvider";
import { ToastProvider } from "../components/ToastProvider";
import { playTestTone, runMicTest } from "../utils/audioTest";
import { deleteVoiceModel, fetchLLMModels, fetchVoiceModels } from "../services/api";

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
const fetchLLMModelsMock = vi.mocked(fetchLLMModels);
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

// `route` lets tests exercise the `?tab=` deep link (defaults to the bare page).
const renderPage = (route = "/configuration") => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <MemoryRouter initialEntries={[route]}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ToastProvider>
            <ConfigurationPage />
          </ToastProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </MemoryRouter>,
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

describe("ConfigurationPage theme select", () => {
  test("lists exactly the themes enabled in the app (no dead options)", async () => {
    renderPage();
    const select = (await screen.findByLabelText("Theme")) as HTMLSelectElement;

    const optionValues = Array.from(select.options).map((o) => o.value);
    // Drives options from AVAILABLE_THEMES — every enabled theme is offered…
    for (const theme of AVAILABLE_THEMES) {
      expect(optionValues).toContain(theme);
    }
    // …and the removed themes are gone.
    expect(optionValues).not.toContain("cyberpunk");
    expect(optionValues).not.toContain("synthwave");
  });

  test("offers the real themes that replaced the removed ones", async () => {
    renderPage();
    await screen.findByLabelText("Theme");
    // Spot-check a couple of the themes that were previously missing.
    expect(screen.getByRole("option", { name: "Corporate" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Nord" })).toBeInTheDocument();
  });

  test("selecting a real theme marks the form dirty", async () => {
    renderPage();
    const select = (await screen.findByLabelText("Theme")) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "nord" } });
    expect(select.value).toBe("nord");
    expect(screen.getByTestId("save-button")).toBeEnabled();
  });
});

describe("ConfigurationPage tab keyboard navigation (APG)", () => {
  const tabNames = [/General/, /Audio/, /Voice Models/, /LLM/];

  const getTabs = () => tabNames.map((n) => screen.getByRole("tab", { name: n }));

  test("uses a roving tabindex: only the active tab is in the tab order", async () => {
    renderPage();
    await screen.findByRole("tab", { name: /General/ });
    const [general, audio, models, llm] = getTabs();

    expect(general).toHaveAttribute("tabindex", "0");
    expect(audio).toHaveAttribute("tabindex", "-1");
    expect(models).toHaveAttribute("tabindex", "-1");
    expect(llm).toHaveAttribute("tabindex", "-1");
  });

  test("ArrowRight/ArrowLeft move (and wrap) the active tab", async () => {
    renderPage();
    const tablist = await screen.findByRole("tablist", { name: "Configuration sections" });

    fireEvent.keyDown(tablist, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: /Audio/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: /Audio/ })).toHaveAttribute("tabindex", "0");

    // Wrap backwards from the first tab to the last.
    fireEvent.keyDown(tablist, { key: "ArrowLeft" });
    fireEvent.keyDown(tablist, { key: "ArrowLeft" });
    expect(screen.getByRole("tab", { name: /LLM/ })).toHaveAttribute("aria-selected", "true");
  });

  test("Home and End jump to the first and last tab", async () => {
    renderPage();
    const tablist = await screen.findByRole("tablist", { name: "Configuration sections" });

    fireEvent.keyDown(tablist, { key: "End" });
    expect(screen.getByRole("tab", { name: /LLM/ })).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tablist, { key: "Home" });
    expect(screen.getByRole("tab", { name: /General/ })).toHaveAttribute("aria-selected", "true");
  });
});

describe("ConfigurationPage URL-backed active tab", () => {
  // Surfaces the live location (path + query) so tests can assert the URL is
  // kept in sync with the active tab.
  const LocationProbe: React.FC = () => {
    const location = useLocation();
    return <div data-testid="location">{location.pathname + location.search}</div>;
  };

  const renderWithLocation = (route = "/configuration") => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return render(
      <MemoryRouter initialEntries={[route]}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <ToastProvider>
              <ConfigurationPage />
              <LocationProbe />
            </ToastProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </MemoryRouter>,
    );
  };

  test("?tab=llm opens the LLM tab on load", async () => {
    renderWithLocation("/configuration?tab=llm");

    const llmTab = await screen.findByRole("tab", { name: /LLM/ });
    expect(llmTab).toHaveAttribute("aria-selected", "true");
    // The LLM panel content is rendered, the General one is not.
    expect(screen.getByText("LLM Endpoint")).toBeInTheDocument();
    expect(screen.queryByText("General Settings")).not.toBeInTheDocument();
  });

  test("an unknown ?tab= falls back to the General tab", async () => {
    renderWithLocation("/configuration?tab=bogus");

    const general = await screen.findByRole("tab", { name: /General/ });
    expect(general).toHaveAttribute("aria-selected", "true");
  });

  test("switching tabs updates the URL (replacing, not pushing)", async () => {
    renderWithLocation("/configuration");

    await screen.findByRole("tab", { name: /Audio/ });
    fireEvent.click(screen.getByRole("tab", { name: /Audio/ }));

    await waitFor(() =>
      expect(screen.getByTestId("location")).toHaveTextContent("/configuration?tab=audio"),
    );
    expect(screen.getByRole("tab", { name: /Audio/ })).toHaveAttribute("aria-selected", "true");

    // Keyboard navigation drives the URL too.
    fireEvent.keyDown(
      screen.getByRole("tablist", { name: "Configuration sections" }),
      { key: "ArrowRight" },
    );
    await waitFor(() =>
      expect(screen.getByTestId("location")).toHaveTextContent("/configuration?tab=models"),
    );
  });
});

describe("ConfigurationPage fetch-models error handling", () => {
  test("a failed model fetch surfaces an error toast and an inline message", async () => {
    fetchLLMModelsMock.mockRejectedValueOnce(new Error("Failed to fetch (CORS)"));

    renderPage();
    await screen.findByRole("tab", { name: /LLM/ });
    goToTab(/LLM/);

    fireEvent.click(screen.getByRole("button", { name: /Fetch list/ }));

    // Inline error + toast, instead of silently doing nothing.
    await screen.findByTestId("model-fetch-error");
    expect(screen.getByTestId("model-fetch-error")).toHaveTextContent("Failed to fetch (CORS)");
    await screen.findByText(/Failed to fetch models: Failed to fetch \(CORS\)/);
  });
});

describe("ConfigurationPage mic-test stream cleanup", () => {
  const installMicStream = () => {
    const track = { stop: vi.fn() };
    const stream = { getTracks: () => [track] } as unknown as MediaStream;
    const getUserMedia = vi.fn().mockResolvedValue(stream);
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia },
    });
    return { track, stream, getUserMedia };
  };

  test("leaving the Audio tab stops an in-progress mic test stream", async () => {
    // Capture the underlying spy: handleTestMic transiently wraps getUserMedia,
    // so navigator.mediaDevices.getUserMedia is the wrapper while a test is in
    // flight — assert on the original spy instead.
    const { track, getUserMedia } = installMicStream();

    // Keep the mic test pending so the stream is "in progress" when we leave.
    let resolveMic!: (r: { peakLevel: number }) => void;
    runMicTestMock.mockImplementation(async () => {
      // Mirror runMicTest: acquire the stream via the (wrapped) getUserMedia so
      // the page captures a handle to stop.
      await navigator.mediaDevices.getUserMedia({ audio: true });
      return new Promise((resolve) => {
        resolveMic = resolve;
      });
    });

    renderPage();
    await screen.findByRole("tab", { name: /Audio/ });
    goToTab(/Audio/);

    fireEvent.click(screen.getByTestId("mic-test-button"));
    // Wait until the (wrapped) getUserMedia has captured the stream handle.
    await waitFor(() => expect(getUserMedia).toHaveBeenCalled());

    // Switch away from the Audio tab mid-test: the stream must be stopped.
    goToTab(/General/);
    expect(track.stop).toHaveBeenCalled();

    // Resolve the lingering promise so React Query/act doesn't warn.
    await act(async () => resolveMic({ peakLevel: 0 }));
  });
});
