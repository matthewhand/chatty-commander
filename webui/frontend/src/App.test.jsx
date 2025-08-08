import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from './App';

// Mock the Dashboard component
jest.mock('./components/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard Component</div>;
  };
});

// Mock the apiService
jest.mock('./services/apiService', () => ({
  apiService: {
    isServerReachable: jest.fn(() => Promise.resolve(true)),
    getVersion: jest.fn(() => Promise.resolve('1.0.0')),
    healthCheck: jest.fn(() => Promise.resolve({ status: 'healthy' }))
  }
}));

const renderApp = () => {
  return render(<App />);
};

describe('App Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    localStorage.clear();
  });

  test('renders without crashing', () => {
    const { container } = renderApp();
    expect(container).toBeInTheDocument();
  });

  test('renders dashboard component', async () => {
    await act(async () => {
      renderApp();
    });
    
    // Check that we don't see the server error message
    expect(screen.queryByText(/Unable to connect to ChattyCommander server/i)).not.toBeInTheDocument();
  });
});