import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import DashboardPage from "./DashboardPage";

// Connected socket, but the last message arrived well beyond the staleness
// threshold (~2x the 5s telemetry interval). The card should downgrade to a
// warning "Stale" presentation even though it is technically connected.
vi.mock("../components/WebSocketProvider", () => ({
  useWebSocket: () => ({
    ws: null,
    isConnected: true,
    reconnectAttempt: 0,
    lastMessageTime: Date.now() - 60_000, // 60s ago → stale
  }),
}));

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  json: async () => data,
});

beforeEach(() => {
  global.fetch = vi.fn(async (input: any) => {
    const url = String(input);
    if (url.includes("/health")) {
      return jsonResponse({
        status: "healthy",
        uptime: "1h",
        commands_executed: 0,
        cpu_usage: "50",
        memory_usage: "50",
      });
    }
    if (url.includes("/dograh/")) {
      return jsonResponse({ available: false, reason: "not configured", health: null });
    }
    return jsonResponse({});
  }) as any;
});

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DashboardPage />
    </QueryClientProvider>,
  );
}

describe("DashboardPage stale WebSocket", () => {
  test("downgrades a connected-but-stale socket to a warning 'Stale' card", async () => {
    renderDashboard();
    await screen.findByText("Healthy");

    const card = await screen.findByTestId("websocket-card");
    await waitFor(() => expect(card).toHaveAttribute("data-ws-state", "stale"));
    expect(screen.getByText("Stale")).toBeInTheDocument();

    // The header-level freshness indicator reflects staleness too.
    const freshness = screen.getByTestId("freshness-indicator");
    expect(freshness.textContent).toMatch(/stale/i);
  });

  test("radial CPU/Memory gauges expose aria-valuenow/min/max and labels", async () => {
    renderDashboard();
    await screen.findByText("Healthy");

    const cpu = screen.getByRole("progressbar", { name: "CPU load" });
    expect(cpu).toHaveAttribute("aria-valuenow", "50");
    expect(cpu).toHaveAttribute("aria-valuemin", "0");
    expect(cpu).toHaveAttribute("aria-valuemax", "100");

    const mem = screen.getByRole("progressbar", { name: "Memory usage" });
    expect(mem).toHaveAttribute("aria-valuenow", "50");
    expect(mem).toHaveAttribute("aria-valuemin", "0");
    expect(mem).toHaveAttribute("aria-valuemax", "100");
  });
});
