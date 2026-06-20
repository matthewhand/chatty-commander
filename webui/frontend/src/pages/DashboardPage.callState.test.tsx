import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import DashboardPage from "./DashboardPage";

// A minimal WebSocket stub that lets the test push message frames.
class FakeWebSocket {
  listeners: Record<string, ((ev: any) => void)[]> = {};
  addEventListener(type: string, cb: (ev: any) => void) {
    (this.listeners[type] ??= []).push(cb);
  }
  removeEventListener(type: string, cb: (ev: any) => void) {
    this.listeners[type] = (this.listeners[type] ?? []).filter((c) => c !== cb);
  }
  emit(data: unknown) {
    const payload = JSON.stringify(data);
    (this.listeners["message"] ?? []).forEach((cb) => cb({ data: payload }));
  }
}

const fakeWs = new FakeWebSocket();

vi.mock("../components/WebSocketProvider", () => ({
  useWebSocket: () => ({
    ws: fakeWs,
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

let callStateSeed: unknown = { state: "unknown", workflow_id: null, run_id: null };

beforeEach(() => {
  global.fetch = vi.fn(async (input: any) => {
    const url = String(input);
    if (url.includes("/dograh/call-state")) {
      return jsonResponse(callStateSeed);
    }
    if (url.includes("/health")) {
      return jsonResponse({
        status: "healthy",
        uptime: "1h",
        commands_executed: 0,
        cpu_usage: "1",
        memory_usage: "1",
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

describe("DashboardPage dograh call state", () => {
  test("stays hidden when there is no active call (unknown)", async () => {
    callStateSeed = { state: "unknown", workflow_id: null, run_id: null };
    renderDashboard();

    await screen.findByText("Healthy");
    expect(screen.queryByTestId("dograh-call-state")).not.toBeInTheDocument();
  });

  test("seeds from GET /api/v1/dograh/call-state on mount", async () => {
    callStateSeed = { state: "ringing", workflow_id: 7, run_id: 99 };
    renderDashboard();

    const badge = await screen.findByTestId("dograh-call-state");
    expect(badge).toHaveAttribute("data-call-state", "ringing");
    expect(screen.getByText("Ringing")).toBeInTheDocument();
    expect(
      (global.fetch as any).mock.calls.some((c: any[]) =>
        String(c[0]).includes("/api/v1/dograh/call-state"),
      ),
    ).toBe(true);
  });

  test("updates live from the dograh_call_state WS frame (ringing -> in_call -> ended)", async () => {
    callStateSeed = { state: "unknown", workflow_id: null, run_id: null };
    renderDashboard();
    await screen.findByText("Healthy");

    act(() => {
      fakeWs.emit({
        type: "dograh_call_state",
        data: { state: "ringing", workflow_id: 1, run_id: 2 },
      });
    });
    await waitFor(() =>
      expect(screen.getByTestId("dograh-call-state")).toHaveAttribute("data-call-state", "ringing"),
    );

    act(() => {
      fakeWs.emit({
        type: "dograh_call_state",
        data: { state: "in_call", workflow_id: 1, run_id: 2 },
      });
    });
    await waitFor(() =>
      expect(screen.getByTestId("dograh-call-state")).toHaveAttribute("data-call-state", "in_call"),
    );
    expect(screen.getByText("In call")).toBeInTheDocument();

    act(() => {
      fakeWs.emit({
        type: "dograh_call_state",
        data: { state: "ended", workflow_id: 1, run_id: 2 },
      });
    });
    await waitFor(() =>
      expect(screen.getByTestId("dograh-call-state")).toHaveAttribute("data-call-state", "ended"),
    );
    expect(screen.getByText("Call ended")).toBeInTheDocument();
  });
});
