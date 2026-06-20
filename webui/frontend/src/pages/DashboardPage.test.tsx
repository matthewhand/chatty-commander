import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import DashboardPage from "./DashboardPage";

// The page consumes the WebSocket context; provide a connected stub.
vi.mock("../components/WebSocketProvider", () => ({
  useWebSocket: () => ({
    ws: null,
    isConnected: true,
    reconnectAttempt: 0,
    lastMessageTime: null,
  }),
}));

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  json: async () => data,
});

beforeEach(() => {
  window.localStorage.clear();
  global.fetch = vi.fn(async (input: any) => {
    const url = String(input);
    if (url.includes("/health")) {
      return jsonResponse({
        status: "healthy",
        uptime: "1h 2m",
        commands_executed: 42,
        version: "0.2.0",
        cpu_usage: "12.5",
        memory_usage: "33.1",
      });
    }
    if (url.includes("/advisors/context/stats")) {
      return jsonResponse({
        contexts: {
          "discord:general:user1": {
            persona_id: "philosophy_advisor",
            last_updated: "2026-06-10T00:00:00Z",
            context_key: "discord:general:user1",
          },
        },
        total: 1,
      });
    }
    if (url.includes("/api/v1/status")) {
      return jsonResponse({ status: "running", current_state: "idle", active_models: [], uptime: "1h" });
    }
    if (url.includes("/dograh/")) {
      return jsonResponse({ available: false, reason: "not configured", health: null });
    }
    return jsonResponse({});
  }) as any;
});

function renderDashboard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  test("renders system stats from the health endpoint", async () => {
    renderDashboard();

    // Skeleton clears once the health query resolves.
    expect(await screen.findByText("Healthy")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Dashboard" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1h 2m")).toBeInTheDocument(); // uptime
    expect(screen.getByText("42")).toBeInTheDocument(); // commands executed
    // CPU/Memory are rounded to whole-percent to match the radial ring label.
    expect(screen.getAllByText("13%").length).toBeGreaterThan(0); // cpu (12.5 → 13%)
    expect(screen.getAllByText("33%").length).toBeGreaterThan(0); // memory (33.1 → 33%)
    expect(document.title).toBe("Dashboard | ChattyCommander");
  });

  test("shows the websocket as connected and lists agents", async () => {
    renderDashboard();

    expect(await screen.findByText("Connected")).toBeInTheDocument();

    // Agent card derived from /api/v1/advisors/context/stats
    expect(
      await screen.findByText("philosophy_advisor @ discord:general:user1"),
    ).toBeInTheDocument();

    // Command input is enabled when the socket is connected.
    expect(
      screen.getByPlaceholderText("Type a command to execute..."),
    ).not.toBeDisabled();
  });

  test("surfaces a voice/listening status card seeded from the status endpoint", async () => {
    renderDashboard();
    const card = await screen.findByTestId("voice-status-card");
    // current_state defaults to "idle" from the stubbed /api/v1/status payload.
    await waitFor(() => expect(card).toHaveAttribute("data-voice-mode", "idle"));
    // The mode is rendered as a real value (not a leaked "unknown" token), and
    // mic — which the backend doesn't report — shows a clean em-dash placeholder.
    expect(card.textContent?.toLowerCase()).toContain("idle");
    expect(card.textContent?.toLowerCase()).not.toContain("unknown");
    expect(card.textContent).toContain("—");
  });

  test("real-time log is an aria-live log region", async () => {
    renderDashboard();
    await screen.findByText("Healthy");
    const log = screen.getByRole("log", { name: "Real-time command log" });
    expect(log).toHaveAttribute("aria-live", "polite");
  });

  test("shows a first-run onboarding callout linking to authoring and voice-test", async () => {
    renderDashboard();
    await screen.findByText("Healthy");

    const callout = screen.getByTestId("onboarding-callout");
    expect(callout).toBeInTheDocument();

    const authorLink = screen.getByRole("link", { name: /author a command/i });
    expect(authorLink).toHaveAttribute("href", "/commands/authoring");

    const testLink = screen.getByRole("link", { name: /test it by voice/i });
    expect(testLink).toHaveAttribute("href", "/voice-test");
  });

  test("onboarding callout dismisses and stays dismissed (persisted)", async () => {
    const { unmount } = renderDashboard();
    await screen.findByText("Healthy");

    fireEvent.click(
      screen.getByRole("button", { name: /dismiss getting started guide/i }),
    );

    await waitFor(() =>
      expect(screen.queryByTestId("onboarding-callout")).not.toBeInTheDocument(),
    );
    expect(window.localStorage.getItem("chatty.onboardingDismissed")).toBe("1");

    // A fresh mount honours the persisted dismissal.
    unmount();
    renderDashboard();
    await screen.findByText("Healthy");
    expect(screen.queryByTestId("onboarding-callout")).not.toBeInTheDocument();
  });
});
