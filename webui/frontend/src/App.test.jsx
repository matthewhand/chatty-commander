import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
    renderApp();
    
    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});