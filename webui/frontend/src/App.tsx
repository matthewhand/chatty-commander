import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Import pages
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ConfigurationPage from "./pages/ConfigurationPage";
import AudioSettingsPage from "./pages/AudioSettingsPage";
import PersonasPage from "./pages/PersonasPage";
import AgentStatusPage from "./pages/AgentStatusPage";

// Import components
import MainLayout from "./components/MainLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import { WebSocketProvider } from "./components/WebSocketProvider";

// Import hooks
import { useAuth } from "./hooks/useAuth";

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function AppContent() {
  const { isAuthenticated } = useAuth();
  const noAuth = process.env.REACT_APP_NO_AUTH === "true";
  const showNav = isAuthenticated || noAuth;

  // Wrapper for protected content that needs the MainLayout
  const ProtectedLayout = () => (
    <ProtectedRoute>
      <MainLayout>
        <Outlet />
      </MainLayout>
    </ProtectedRoute>
  );

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            showNav ? <Navigate to="/dashboard" replace /> : <LoginPage />
          }
        />

        {/* Protected Routes (Wrapped in MainLayout) */}
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/configuration" element={<ConfigurationPage />} />
          <Route path="/audio-settings" element={<AudioSettingsPage />} />
          <Route path="/personas" element={<PersonasPage />} />
          <Route path="/agent-status" element={<AgentStatusPage />} />
        </Route>

        {/* Default Redirect */}
        <Route
          path="/"
          element={
            <Navigate to={showNav ? "/dashboard" : "/login"} replace />
          }
        />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        <div data-theme="dark" className="min-h-screen bg-base-100 text-base-content">
          <AppContent />
        </div>
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export default App;
