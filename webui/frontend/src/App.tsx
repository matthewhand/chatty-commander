import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ConfigurationPage from './pages/ConfigurationPage';
import AudioSettingsPage from './pages/AudioSettingsPage';
import PersonasPage from './pages/PersonasPage';

// Import components
import Navigation from './components/Navigation';
import ProtectedRoute from './components/ProtectedRoute';
import { WebSocketProvider } from './components/WebSocketProvider';

// Import hooks
import { useAuth } from './hooks/useAuth';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create Material-UI theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function AppContent() {
  const { isAuthenticated } = useAuth();
  const noAuth = process.env.REACT_APP_NO_AUTH === 'true';
  const showNav = isAuthenticated || noAuth;

  return (
    <Router>
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {showNav && <Navigation />}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: showNav ? 3 : 0,
            ml: showNav ? '240px' : 0,
          }}
        >
          <Routes>
            <Route
              path="/login"
              element={
                (isAuthenticated || noAuth) ? <Navigate to="/dashboard" replace /> : <LoginPage />
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/configuration"
              element={
                <ProtectedRoute>
                  <ConfigurationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audio-settings"
              element={
                <ProtectedRoute>
                  <AudioSettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/personas"
              element={
                <ProtectedRoute>
                  <PersonasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/"
              element={
                <Navigate to={(isAuthenticated || noAuth) ? '/dashboard' : '/login'} replace />
              }
            />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <WebSocketProvider>
          <AppContent />
        </WebSocketProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;