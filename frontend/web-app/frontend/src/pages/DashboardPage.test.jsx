import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import DashboardPage from "./DashboardPage";
import { WebSocketProvider } from "../components/WebSocketProvider";

// Mock the useWebSocket hook to match the hook's actual API
jest.mock("../hooks/useWebSocket", () => ({
  __esModule: true,
  useWebSocket: () => ({
    isConnected: true,
    connectionStatus: "OPEN",
    lastMessage: null,
    sendMessage: jest.fn(),
    reconnectAttempts: 0,
    error: null,
    connect: jest.fn(),
    disconnect: jest.fn(),
    reconnect: jest.fn(),
    getReadyState: jest.fn(() => 1),
    getReadyStateString: jest.fn(() => "OPEN"),
  }),
}));

// Mock the apiService with predictable responses
jest.mock("../services/apiService", () => ({
  healthCheck: jest.fn(() => Promise.resolve({ status: "healthy" })),
  getStatus: jest.fn(() =>
    Promise.resolve({
      state: "idle",
      models: { chatty: "loaded", computer: "loaded" },
    }),
  ),
  getConfig: jest.fn(() =>
    Promise.resolve({
      voice_recognition: { enabled: true },
      audio: { input_device: "default" },
    }),
  ),
}));

const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <DashboardPage />
      </WebSocketProvider>
    </QueryClientProvider>,
  );
};

describe("Dashboard Component", () => {
  test("renders dashboard with system status", async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/status/i)).toBeInTheDocument();
    });
  });

  test("displays WebSocket connection card text", async () => {
    renderDashboard();

    // Use findAllByText to allow multiple matches; assert at least one exists
    const els = await screen.findAllByText(
      /websocket|status|uptime|commands executed|online|disconnected/i,
    );
    expect(els.length).toBeGreaterThan(0);
  });

  test("shows loading state initially", () => {
    renderDashboard();

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  test("handles API errors gracefully", async () => {
    const apiService = require("../services/apiService");
    apiService.getStatus.mockRejectedValueOnce(new Error("API Error"));

    renderDashboard();

    // Assert that the page renders a stable element even if a query fails
    await waitFor(() => {
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });
});
