import React from "react";
import { render, screen, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import DograhStatusCard from "./DograhStatusCard";

// A minimal WebSocket stub that lets the test push `dograh_status` frames.
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

vi.mock("./WebSocketProvider", () => ({
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

beforeEach(() => {
  // Default: dograh unconfigured. The card seeds from this on first load.
  global.fetch = vi.fn(async (input: any) => {
    const url = String(input);
    if (url.includes("/dograh/workflows")) {
      return jsonResponse([{ id: 1, name: "wf", status: "ok" }]);
    }
    if (url.includes("/dograh/status")) {
      return jsonResponse({ available: false, reason: "not configured", health: null });
    }
    return jsonResponse({});
  }) as any;
});

function renderCard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DograhStatusCard />
    </QueryClientProvider>,
  );
}

describe("DograhStatusCard", () => {
  test("seeds offline from GET /api/v1/dograh/status on first load", async () => {
    renderCard();
    const card = await screen.findByTestId("dograh-status-card");
    expect(card).toHaveAttribute("data-dograh-state", "unavailable");
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  test("renders online from a pushed `dograh_status` WS frame", async () => {
    renderCard();
    // Wait for the seeded (offline) render so we know the listener is attached.
    await screen.findByTestId("dograh-status-card");

    act(() => {
      fakeWs.emit({
        type: "dograh_status",
        data: { available: true, reason: null, health: { status: "ok", version: "1.2.3" } },
      });
    });

    const card = await screen.findByTestId("dograh-status-card");
    await waitFor(() =>
      expect(card).toHaveAttribute("data-dograh-state", "online"),
    );
    expect(screen.getByText("v1.2.3")).toBeInTheDocument();
    // Workflows query is enabled only once available; it reports the count.
    await waitFor(() => expect(screen.getByText("1 workflow")).toBeInTheDocument());
  });

  test("pushed status overrides the seeded value (online -> offline)", async () => {
    renderCard();
    await screen.findByTestId("dograh-status-card");

    act(() => {
      fakeWs.emit({
        type: "dograh_status",
        data: { available: true, reason: null, health: { version: "9.9.9" } },
      });
    });
    await waitFor(() =>
      expect(screen.getByTestId("dograh-status-card")).toHaveAttribute("data-dograh-state", "online"),
    );

    act(() => {
      fakeWs.emit({
        type: "dograh_status",
        data: { available: false, reason: "unreachable", health: null },
      });
    });
    await waitFor(() =>
      expect(screen.getByTestId("dograh-status-card")).toHaveAttribute("data-dograh-state", "unavailable"),
    );
  });
});
