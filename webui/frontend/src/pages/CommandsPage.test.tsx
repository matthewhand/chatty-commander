import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";
import CommandsPage from "./CommandsPage";
import { apiService } from "../services/apiService";

vi.mock("../services/apiService", () => ({
  apiService: { getCommands: vi.fn() },
}));

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CommandsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  (apiService.getCommands as ReturnType<typeof vi.fn>).mockResolvedValue({
    take_screenshot: { action: "keypress", keys: "alt+print_screen" },
    open_docs: { action: "url", url: "https://example.com/docs" },
  });
});

test("each command card shows its name", async () => {
  renderPage();
  // The command name is the card title (previously the card was anonymous).
  expect(await screen.findByText("take_screenshot")).toBeInTheDocument();
  expect(await screen.findByText("open_docs")).toBeInTheDocument();
});

test("each card describes the command's actual action", async () => {
  renderPage();
  // keypress command shows the keys it presses
  expect(await screen.findByText("Presses keys")).toBeInTheDocument();
  expect(await screen.findByText("alt+print_screen")).toBeInTheDocument();
  // url command shows the URL it opens
  expect(await screen.findByText("Opens URL")).toBeInTheDocument();
  expect(
    await screen.findByText("https://example.com/docs")
  ).toBeInTheDocument();
});
