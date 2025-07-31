import { renderHook, act } from '@testing-library/react';
import { useAuth } from './useAuth';

// Mock authService
jest.mock('../services/authService', () => ({
  login: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  getToken: jest.fn(),
  setToken: jest.fn(),
  removeToken: jest.fn()
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('initializes with no user', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.loading).toBe(true);
  });

  test('handles login successfully', async () => {
    const mockUser = { username: 'testuser', id: 1 };
    const authService = require('../services/authService');
    authService.login.mockResolvedValueOnce({ user: mockUser, token: 'test-token' });
    
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

  test('checks for existing token on mount', () => {
    const authService = require('../services/authService');
    authService.getToken.mockReturnValueOnce('existing-token');
    authService.getCurrentUser.mockReturnValueOnce({ username: 'existing-user' });
    
    const { result } = renderHook(() => useAuth());
    
    expect(authService.getToken).toHaveBeenCalled();
  });
});