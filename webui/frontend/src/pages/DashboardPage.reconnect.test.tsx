import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import DashboardPage from "./DashboardPage";

// Automatic reconnection has been exhausted: the socket is offline and the
// provider has flipped reconnectExhausted. The dashboard should surface a
// "Connection lost" state plus a Reconnect button wired to reconnect().
const reconnectSpy = vi.fn();

vi.mock("../components/WebSocketProvider", () => ({
  useWebSocket: () => ({
    ws: null,
    isConnected: false,
    reconnectAttempt: 10,
    lastMessageTime: null,
    reconnectExhausted: true,
    reconnect: reconnectSpy,
  }),
}));

const jsonResponse = (data: unknown) => ({
  ok: true,
  status: 200,
  json: async () => data,
});

beforeEach(() => {
  reconnectSpy.mockClear();
  window.localStorage.clear();
  global.fetch = vi.fn(async (input: any) => {
    const url = String(input);
    if (url.includes("/health")) {
      return jsonResponse({
        status: "healthy",
        uptime: "1h",
        commands_executed: 0,
        cpu_usage: "10",
        memory_usage: "20",
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
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage reconnect-exhausted", () => {
  test("WebSocket card shows 'Connection lost' and a Reconnect button that calls reconnect()", async () => {
    renderDashboard();
    await screen.findByText("Healthy");

    const card = await screen.findByTestId("websocket-card");
    expect(card).toHaveAttribute("data-ws-state", "lost");
    expect(screen.getByText("Connection lost")).toBeInTheDocument();

    const button = screen.getByTestId("ws-reconnect-button");
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(reconnectSpy).toHaveBeenCalledTimes(1);
  });

  test("command-log offline notice offers a Reconnect button wired to reconnect()", async () => {
    renderDashboard();
    await screen.findByText("Healthy");

    const button = await screen.findByTestId("log-reconnect-button");
    fireEvent.click(button);
    expect(reconnectSpy).toHaveBeenCalledTimes(1);
  });
});
