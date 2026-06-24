import React from "react";
import { render, screen, waitFor, within, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import CommandAuthoringPage, {
  detectShellDanger,
  detectUrlDanger,
  collectDangerFlags,
  validateAction,
} from "./CommandAuthoringPage";
import { ToastProvider } from "../components/ToastProvider";
import {
  hasUnsavedChanges,
  __resetUnsavedChanges,
} from "../hooks/useUnsavedChanges";

// --- Pure heuristic unit tests (no DOM) ---

describe("detectShellDanger", () => {
  test("flags rm -rf", () => {
    expect(detectShellDanger("rm -rf /tmp/x")).toMatch(/recursive|delete/i);
    expect(detectShellDanger("rm -fr ~/data")).toMatch(/delete/i);
  });
  test("flags curl|sh", () => {
    expect(detectShellDanger("curl https://x.sh | sh")).toMatch(/remote code/i);
    expect(detectShellDanger("wget -qO- http://x | bash")).toMatch(/remote code/i);
  });
  test("flags sudo", () => {
    expect(detectShellDanger("sudo apt-get install foo")).toMatch(/elevated/i);
  });
  test("passes benign commands", () => {
    expect(detectShellDanger("npm start")).toBeNull();
    expect(detectShellDanger("echo hello")).toBeNull();
    expect(detectShellDanger("")).toBeNull();
  });
});

describe("detectUrlDanger", () => {
  test("https passes", () => {
    expect(detectUrlDanger("https://example.com")).toBeNull();
  });
  test("http on localhost passes", () => {
    expect(detectUrlDanger("http://localhost:3000/x")).toBeNull();
    expect(detectUrlDanger("http://127.0.0.1:8000")).toBeNull();
  });
  test("http on remote host is flagged", () => {
    expect(detectUrlDanger("http://example.com")).toMatch(/insecure/i);
  });
  test("missing scheme is flagged", () => {
    expect(detectUrlDanger("example.com")).toMatch(/scheme/i);
  });
});

describe("validateAction", () => {
  test("keypress requires keys", () => {
    expect(validateAction({ type: "keypress" })).toMatch(/keys/i);
    expect(validateAction({ type: "keypress", keys: "ctrl+t" })).toBeNull();
  });
  test("shell accepts cmd or command", () => {
    expect(validateAction({ type: "shell", command: "ls" })).toBeNull();
    expect(validateAction({ type: "shell" })).toMatch(/command/i);
  });
});

describe("collectDangerFlags", () => {
  test("aggregates flagged shell + url actions with indexes", () => {
    const flags = collectDangerFlags([
      { type: "keypress", keys: "ctrl+t" },
      { type: "shell", cmd: "rm -rf /" },
      { type: "url", url: "http://evil.com" },
    ]);
    expect(flags.map((f) => f.index)).toEqual([1, 2]);
  });
});

// --- Component tests ---

const config = {
  commands: {
    existing_cmd: { name: "Existing", actions: [{ type: "keypress", keys: "ctrl+a" }] },
  },
};

function mockFetch() {
  return vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/v1/config" && (!init || init.method !== "PUT")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(config),
      } as Response);
    }
    if (url === "/api/v1/config" && init?.method === "PUT") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) } as Response);
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
  });
}

function renderPage(initialEntries: string[] = ["/authoring"]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/authoring" element={<CommandAuthoringPage />} />
            <Route path="/commands" element={<div>Commands List Page</div>} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch());
  __resetUnsavedChanges();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  __resetUnsavedChanges();
});

async function fillManualForm(name: string) {
  fireEvent.click(screen.getByRole("tab", { name: /Manual Mode/i }));
  fireEvent.change(screen.getByLabelText(/Command Name/i), {
    target: { value: name },
  });
  fireEvent.change(screen.getByLabelText(/Display Name/i), {
    target: { value: "Display" },
  });
  fireEvent.change(screen.getByLabelText(/Wakeword/i), {
    target: { value: "trigger" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Add Action/i }));
  fireEvent.change(screen.getByLabelText("Keys"), {
    target: { value: "ctrl+alt+t" },
  });
}

describe("collision warning", () => {
  test("blocks saving a command whose name already exists", async () => {
    renderPage();
    // Wait for existing names to load.
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    await fillManualForm("existing_cmd");

    fireEvent.click(screen.getByRole("button", { name: /Save Command/i }));

    expect(await screen.findByText(/already exists/i)).toBeInTheDocument();
    // Confirm modal must NOT have opened.
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  test("allows saving a uniquely named command", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    await fillManualForm("brand_new");

    fireEvent.click(screen.getByRole("button", { name: /Save Command/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.queryByText(/already exists/i)).not.toBeInTheDocument();
  });
});

describe("modal a11y", () => {
  test("Escape closes the dialog and it has dialog semantics", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    await fillManualForm("brand_new");
    fireEvent.click(screen.getByRole("button", { name: /Save Command/i }));

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby");
    // Cancel button receives focus on open.
    const cancel = within(dialog).getByRole("button", { name: /^Cancel$/i });
    await waitFor(() => expect(cancel).toHaveFocus());

    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    );
  });
});

describe("mode tabs a11y (WAI-ARIA APG)", () => {
  test("uses roving tabindex with the active tab focusable", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));

    const aiTab = screen.getByRole("tab", { name: /AI Mode/i });
    const manualTab = screen.getByRole("tab", { name: /Manual Mode/i });

    // AI mode is active by default: active tab tabIndex=0, other tabIndex=-1.
    expect(aiTab).toHaveAttribute("aria-selected", "true");
    expect(aiTab).toHaveAttribute("tabindex", "0");
    expect(manualTab).toHaveAttribute("aria-selected", "false");
    expect(manualTab).toHaveAttribute("tabindex", "-1");

    // Panel is wired to its tab.
    const panel = screen.getByRole("tabpanel");
    expect(panel).toHaveAttribute("aria-labelledby", "tab-ai-mode");
  });

  test("ArrowRight/Left move selection and focus between tabs", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));

    const aiTab = screen.getByRole("tab", { name: /AI Mode/i });
    const manualTab = screen.getByRole("tab", { name: /Manual Mode/i });

    aiTab.focus();
    fireEvent.keyDown(aiTab, { key: "ArrowRight" });

    // Selection follows focus: Manual becomes active and focused.
    await waitFor(() => expect(manualTab).toHaveAttribute("aria-selected", "true"));
    expect(manualTab).toHaveAttribute("tabindex", "0");
    expect(aiTab).toHaveAttribute("tabindex", "-1");
    expect(manualTab).toHaveFocus();
    // Manual panel is now shown.
    expect(screen.getByRole("tabpanel")).toHaveAttribute(
      "aria-labelledby",
      "tab-manual-mode"
    );

    // ArrowLeft moves back to AI.
    fireEvent.keyDown(manualTab, { key: "ArrowLeft" });
    await waitFor(() => expect(aiTab).toHaveAttribute("aria-selected", "true"));
    expect(aiTab).toHaveFocus();
  });

  test("Home/End jump to the first/last tab", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));

    const aiTab = screen.getByRole("tab", { name: /AI Mode/i });
    const manualTab = screen.getByRole("tab", { name: /Manual Mode/i });

    aiTab.focus();
    fireEvent.keyDown(aiTab, { key: "End" });
    await waitFor(() => expect(manualTab).toHaveAttribute("aria-selected", "true"));
    expect(manualTab).toHaveFocus();

    fireEvent.keyDown(manualTab, { key: "Home" });
    await waitFor(() => expect(aiTab).toHaveAttribute("aria-selected", "true"));
    expect(aiTab).toHaveFocus();
  });
});

describe("per-action validation a11y", () => {
  test("invalid action input is wired to its error via aria-describedby", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    fireEvent.click(screen.getByRole("tab", { name: /Manual Mode/i }));
    // A fresh keypress action has no keys yet → validation error present.
    fireEvent.click(screen.getByRole("button", { name: /Add Action/i }));

    const keysInput = screen.getByLabelText("Keys");
    expect(keysInput).toHaveAttribute("aria-invalid", "true");
    const describedBy = keysInput.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    const errorEl = document.getElementById(describedBy as string) /* eslint-disable-line testing-library/no-node-access */;
    expect(errorEl).not.toBeNull();
    expect(errorEl).toHaveAttribute("role", "alert");

    // Once a valid value is entered, the wiring is removed.
    fireEvent.change(keysInput, { target: { value: "ctrl+alt+t" } });
    expect(screen.getByLabelText("Keys")).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText("Keys")).not.toHaveAttribute("aria-describedby");
  });
});

describe("danger warnings", () => {
  test("inline warning shown for rm -rf shell command", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    fireEvent.click(screen.getByRole("tab", { name: /Manual Mode/i }));
    fireEvent.click(screen.getByRole("button", { name: /Add Action/i }));
    // Switch the action to shell.
    fireEvent.change(screen.getByLabelText("Type"), {
      target: { value: "shell" },
    });
    fireEvent.change(screen.getByLabelText("Command"), {
      target: { value: "rm -rf /tmp/x" },
    });

    expect(await screen.findByText(/recursive|delete/i)).toBeInTheDocument();
  });
});

describe("success path", () => {
  test("navigates to /commands after a successful save", async () => {
    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    await fillManualForm("brand_new");
    fireEvent.click(screen.getByRole("button", { name: /Save Command/i }));

    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: /Confirm Save/i }));

    expect(await screen.findByText("Commands List Page")).toBeInTheDocument();
  });
});

describe("dirty tracking (unsaved-changes gate)", () => {
  test("AI mode is not dirty until a command is generated", async () => {
    // Generate endpoint returns a command so we can flip from clean → dirty.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        if (url === "/api/v1/commands/generate") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                name: "made_up",
                display_name: "Made Up",
                wakeword: "go",
                actions: [{ type: "keypress", keys: "ctrl+x" }],
              }),
          } as Response);
        }
        if (url === "/api/v1/config" && (!init || init.method !== "PUT")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(config),
          } as Response);
        }
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
      })
    );

    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));

    // Typing a half-written prompt must NOT mark the form dirty — there is
    // nothing savable yet, so the session-expiry deferral shouldn't trip.
    fireEvent.change(screen.getByLabelText(/Command Description/i), {
      target: { value: "open my email" },
    });
    expect(hasUnsavedChanges()).toBe(false);

    // Generating produces a savable result → now it's dirty.
    fireEvent.click(screen.getByRole("button", { name: /Generate Command/i }));
    await waitFor(() => expect(hasUnsavedChanges()).toBe(true));
  });

  test("manual edit-then-revert reads as clean (no phantom dirty)", async () => {
    // Load an existing command for editing; its baseline is normalized through
    // the same mapper saveCommand uses, so reverting an edit returns to clean.
    renderPage(["/authoring?edit=existing_cmd"]);

    // Wait for the loaded command to populate the form.
    await waitFor(() =>
      expect((screen.getByLabelText(/Display Name/i) as HTMLInputElement).value).toBe(
        "Existing"
      )
    );
    // Freshly loaded definition is the pristine baseline → not dirty.
    await waitFor(() => expect(hasUnsavedChanges()).toBe(false));

    const displayInput = screen.getByLabelText(/Display Name/i) as HTMLInputElement;
    // Edit a field → dirty.
    fireEvent.change(displayInput, { target: { value: "Existing!" } });
    await waitFor(() => expect(hasUnsavedChanges()).toBe(true));

    // Revert the edit → back to clean, despite the server shape (command→cmd,
    // singular action) differing from the in-memory editor shape.
    fireEvent.change(displayInput, { target: { value: "Existing" } });
    await waitFor(() => expect(hasUnsavedChanges()).toBe(false));
  });
});

describe("save-time collision re-check", () => {
  test("blocks a name created in another session after this page loaded", async () => {
    // The mount snapshot sees only `existing_cmd`. A later config fetch (the one
    // performed by the save handler) also returns `late_cmd`, simulating another
    // tab creating it after load — the guard must catch it.
    let configReads = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        if (url === "/api/v1/config" && (!init || init.method !== "PUT")) {
          configReads += 1;
          // First read (mount) → only existing_cmd. Subsequent reads → also late_cmd.
          const commands =
            configReads <= 1
              ? config.commands
              : { ...config.commands, late_cmd: { name: "Late", actions: [] } };
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ commands }),
          } as Response);
        }
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
      })
    );

    renderPage();
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/v1/config"));
    // `late_cmd` was not in the mount snapshot, so the stale guard would miss it.
    await fillManualForm("late_cmd");

    fireEvent.click(screen.getByRole("button", { name: /Save Command/i }));

    expect(await screen.findByText(/already exists/i)).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
