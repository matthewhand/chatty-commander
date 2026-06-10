import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ConfigurationPage from './ConfigurationPage';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../components/ThemeProvider';
import { ToastProvider } from '../components/ToastProvider';
import * as api from '../services/api';

// Mock the API methods directly to avoid fetch complexity
vi.mock('../services/api', () => ({
  fetchLLMModels: vi.fn(),
  fetchVoiceModels: vi.fn(() => Promise.resolve([])),
  uploadVoiceModel: vi.fn(),
  deleteVoiceModel: vi.fn(),
}));

global.fetch = vi.fn();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <ToastProvider>
            {component}
          </ToastProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('ConfigurationPage Async State', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    queryClient.clear();
    // @ts-expect-error Mocking global fetch for testing purposes
    global.fetch.mockImplementation((url: string) => {
      if (url === '/api/v1/config') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        });
      }
      if (url === '/api/v1/audio/devices') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ input: [], output: [] }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  it('displays loading state, then success when models fetch successfully', async () => {
    renderWithProviders(<ConfigurationPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch list/i })).toBeInTheDocument();
    });

    const fetchButton = screen.getByRole('button', { name: /fetch list/i });

    // Mock successful fetch via api.ts
    vi.mocked(api.fetchLLMModels).mockResolvedValueOnce(['model-a', 'model-b']);

    fireEvent.click(fetchButton);

    expect(screen.getByRole('button', { name: /fetching/i })).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /model/i })).toBeInTheDocument();
    });
  });

  it('displays error state when fetching models fails', async () => {
    renderWithProviders(<ConfigurationPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch list/i })).toBeInTheDocument();
    });

    const fetchButton = screen.getByRole('button', { name: /fetch list/i });

    vi.mocked(api.fetchLLMModels).mockRejectedValueOnce(new Error('Network connection failed'));

    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    });
  });

  it('displays empty state when fetching models returns no data', async () => {
    renderWithProviders(<ConfigurationPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch list/i })).toBeInTheDocument();
    });

    const fetchButton = screen.getByRole('button', { name: /fetch list/i });

    vi.mocked(api.fetchLLMModels).mockResolvedValueOnce([]);

    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText('No models returned — check endpoint/key')).toBeInTheDocument();
    });
  });
});
