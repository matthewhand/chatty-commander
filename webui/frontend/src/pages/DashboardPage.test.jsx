import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from './DashboardPage';
import { WebSocketProvider } from '../components/WebSocketProvider';

// Mock the useWebSocket hook
jest.mock('../hooks/useWebSocket', () => ({
  __esModule: true,
  default: () => ({
    isConnected: true,
    lastMessage: null,
    sendMessage: jest.fn(),
    connectionState: 'Connected'
  })
}));

// Mock the apiService
jest.mock('../services/apiService', () => ({
  healthCheck: jest.fn(() => Promise.resolve({ status: 'healthy' })),
  getStatus: jest.fn(() => Promise.resolve({ 
    state: 'idle',
    models: { chatty: 'loaded', computer: 'loaded' }
  })),
  getConfig: jest.fn(() => Promise.resolve({ 
    voice_recognition: { enabled: true },
    audio: { input_device: 'default' }
  }))
}));

const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <DashboardPage />
      </WebSocketProvider>
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders dashboard with system status', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/status/i)).toBeInTheDocument();
    });
  });

  test('displays WebSocket connection status', () => {
    renderDashboard();
    
    expect(screen.getByText(/connected/i)).toBeInTheDocument();
  });

  test('shows loading state initially', () => {
    renderDashboard();
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    // Mock API error
    const apiService = require('../services/apiService');
    apiService.getStatus.mockRejectedValueOnce(new Error('API Error'));
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});