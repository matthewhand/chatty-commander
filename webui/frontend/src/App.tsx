import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Suspense, lazy } from "react";

// Import components
import MainLayout from "./components/MainLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import { WebSocketProvider } from "./components/WebSocketProvider";

// Import hooks
import { useAuth, AuthProvider } from "./hooks/useAuth";
import { ThemeProvider } from "./components/ThemeProvider";

// Lazy load pages for code splitting to reduce main bundle size
const LoginPage = lazy(() => import("./pages/LoginPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const ConfigurationPage = lazy(() => import("./pages/ConfigurationPage"));
const CommandsPage = lazy(() => import("./pages/CommandsPage"));
const CommandAuthoringPage = lazy(() => import("./pages/CommandAuthoringPage"));

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
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner text-primary loading-lg"></span>
      </div>
    );
  }

  // Use a special user object or flag provided by the updated authService to skip login
  const isNoAuthMode = user?.noAuth === true;
  const showNav = isAuthenticated || isNoAuthMode;

  // Wrapper for protected content that needs the MainLayout
  const ProtectedLayout = () => (
    <ProtectedRoute>
      <MainLayout>
        <Suspense fallback={
          <div className="flex-1 flex items-center justify-center p-12 h-full">
            <span className="loading loading-spinner text-primary loading-lg"></span>
          </div>
        }>
          <Outlet />
        </Suspense>
      </MainLayout>
    </ProtectedRoute>
  );

  return (
    <Router>
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center">
          <span className="loading loading-spinner text-primary loading-lg"></span>
        </div>
      }>
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
          <Route path="/commands" element={<CommandsPage />} />
          <Route path="/commands/authoring" element={<CommandAuthoringPage />} />
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
      </Suspense>
    </Router>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <WebSocketProvider>
            <div className="min-h-screen bg-base-100 text-base-content">
              <AppContent />
            </div>
          </WebSocketProvider>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
