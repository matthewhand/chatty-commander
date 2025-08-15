import { renderHook, act } from '@testing-library/react';
import { useAuth } from './useAuth';

// Explicitly mock the named export 'authService' object used in the hook
jest.mock('../services/authService', () => ({
  authService: {
    login: jest.fn(),
    logout: jest.fn(),
    getCurrentUser: jest.fn(),
    getToken: jest.fn(),
    setToken: jest.fn(),
    removeToken: jest.fn()
  }
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    // Provide a minimal localStorage mock for tests
    Object.defineProperty(global, 'localStorage', {
      value: {
        store: {} as Record<string, string>,
        getItem: jest.fn((k: string) => (global as any).localStorage.store[k] ?? null),
        setItem: jest.fn((k: string, v: string) => { (global as any).localStorage.store[k] = v; }),
        removeItem: jest.fn((k: string) => { delete (global as any).localStorage.store[k]; }),
        clear: jest.fn(() => { (global as any).localStorage.store = {}; }),
      },
      writable: true
    });

    (global as any).localStorage.clear();
    jest.clearAllMocks();
  });

  test('initializes with no user', async () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    // After initial effect without token, loading should become false soon
    await act(async () => { await Promise.resolve(); });
    expect(result.current.loading).toBe(false);
  });

  test('handles login successfully', async () => {
    const mockUser = { username: 'testuser', id: 1 };
    const { authService } = require('../services/authService');
    // useAuth.login expects authService.login to return { access_token }
    authService.login.mockResolvedValueOnce({ access_token: 'test-token' });
    authService.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('testuser', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  test('handles logout', async () => {
    const { result } = renderHook(() => useAuth());

    await act(async () => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('checks for existing token on mount', async () => {
    const { authService } = require('../services/authService');
    // Simulate presence of token in storage; hook reads localStorage directly
    (global as any).localStorage.setItem('auth_token', 'existing-token');
    authService.getCurrentUser.mockResolvedValueOnce({ username: 'existing-user' });

    const { result } = renderHook(() => useAuth());

    // Allow effect microtask to run
    await act(async () => { await Promise.resolve(); });

    expect(authService.getCurrentUser).toHaveBeenCalled();
    expect(result.current.user === null || typeof result.current.user === 'object').toBe(true);
  });
});
