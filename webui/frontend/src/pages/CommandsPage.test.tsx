import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi, beforeEach } from 'vitest';
import CommandsPage from './CommandsPage';

vi.mock('../services/apiService', () => ({
  apiService: {
    getCommands: vi.fn().mockResolvedValue({
      take_screenshot: {
        action: 'system',
        cmd: 'flameshot gui'
      },
      open_browser: {
        action: 'url',
        url: 'https://example.com'
      }
    }),
    deleteCommand: vi.fn().mockResolvedValue(true)
  }
}));

// Mock the React Query hooks directly so we don't need a full QueryClientProvider wrapper
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn().mockReturnValue({
    data: {
      take_screenshot: { action: 'system', cmd: 'flameshot gui' },
      open_browser: { action: 'url', url: 'https://example.com' }
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn()
  })
}));

let mockReducedMotion = false;
vi.mock('../hooks/useReducedMotionPref', () => ({
  useReducedMotionPref: () => mockReducedMotion
}));

beforeEach(() => {
  mockReducedMotion = false;
});

test("renders the commands page header", async () => {
  render(
    <MemoryRouter>
      <CommandsPage />
    </MemoryRouter>
  );

  await waitFor(() => {
    expect(screen.getByText("Commands & Triggers")).toBeInTheDocument();
  });
});

test("each command card shows its name", async () => {
  render(<MemoryRouter><CommandsPage /></MemoryRouter>);
  await screen.findByText("take_screenshot");
  expect(screen.getByText("open_browser")).toBeInTheDocument();
});

test("each card describes the command's actual action", async () => {
  render(<MemoryRouter><CommandsPage /></MemoryRouter>);
  await screen.findByText("take_screenshot");

  // Look for the descriptive text in the badges
  expect(screen.getByText("Runs command")).toBeInTheDocument();
  expect(screen.getByText("Opens URL")).toBeInTheDocument();

  // Look for the detail text
  expect(screen.getByText("flameshot gui")).toBeInTheDocument();
  expect(screen.getByText("https://example.com")).toBeInTheDocument();
});

test("respects prefers-reduced-motion: reduce on the card cascade", async () => {
  mockReducedMotion = true;

  render(<MemoryRouter><CommandsPage /></MemoryRouter>);
  await screen.findByText("take_screenshot");

  // We find elements with data-reduced-motion=true using testing-library's query
  const cards = screen.getAllByTestId('command-card-motion');
  expect(cards.length).toBeGreaterThan(0);

  cards.forEach((card) => {
    // The reduced-motion branch must be taken for every cascade card...
    expect(card.getAttribute("data-reduced-motion")).toBe("true");
  });
});

test("applies the staggered cascade when motion is allowed", async () => {
  mockReducedMotion = false;
  render(<MemoryRouter><CommandsPage /></MemoryRouter>);
  await screen.findByText("take_screenshot");

  const cards = screen.getAllByTestId('command-card-motion');
  expect(cards.length).toBeGreaterThan(0);
  cards.forEach((card) => {
    expect(card.getAttribute("data-reduced-motion")).toBe("false");
  });
});
