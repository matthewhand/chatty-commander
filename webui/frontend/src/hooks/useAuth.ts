import { useState, useEffect, createContext, useContext } from 'react';
import { authService } from '../services/authService';

interface User {
  username: string;
  roles: string[];
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  // Always call hooks at the top level
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Only run if context is not available
    if (!context) {
      // Check for existing token on mount
      const token = localStorage.getItem('auth_token');
      if (token) {
        authService.getCurrentUser()
          .then(userData => {
            setUser(userData);
          })
          .catch(() => {
            localStorage.removeItem('auth_token');
          })
          .finally(() => {
            setLoading(false);
          });
      } else {
        setLoading(false);
      }
    }
  }, [context]);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await authService.login(username, password);
      localStorage.setItem('auth_token', response.access_token);
      
      const userData = await authService.getCurrentUser();
      setUser(userData);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  // Return context if available, otherwise return local state
  if (context) {
    return context;
  }

  return {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading
  };
};

export const AuthProvider = AuthContext.Provider;