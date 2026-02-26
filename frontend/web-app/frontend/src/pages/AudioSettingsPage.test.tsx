import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AudioSettingsPage from "./AudioSettingsPage";

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

function renderWithClient(ui: React.ReactElement) {
  const testQueryClient = createTestQueryClient();
  const { rerender, ...result } = render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  );
  return {
    ...result,
    rerender: (rerenderUi: React.ReactElement) =>
      rerender(
        <QueryClientProvider client={testQueryClient}>
          {rerenderUi}
        </QueryClientProvider>
      ),
  };
}

describe("AudioSettingsPage", () => {
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleSpy = jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  test("checks console log usage", async () => {
    renderWithClient(<AudioSettingsPage />);

    // Wait for the query to resolve
    expect(await screen.findByText("Audio Devices")).toBeInTheDocument();

    // Ensure console.log was not called
    expect(consoleSpy).not.toHaveBeenCalledWith("Fetching audio devices...");
    expect(consoleSpy).not.toHaveBeenCalledWith(expect.stringContaining("Saving audio settings"));
  });
});
