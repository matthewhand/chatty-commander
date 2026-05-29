import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

type ProtectedRouteProps = {
  children: React.ReactNode;
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, user, loading } = useAuth();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" role="status" aria-live="polite" aria-label="Verifying authentication">
        <span className="loading loading-spinner loading-lg text-primary" aria-hidden="true"></span>
        <span className="ml-3 text-base-content/60">Verifying authentication...</span>
      </div>
    );
  }

  // Allow bypassing auth in development/no-auth mode based on dynamic backend configuration
  if (user?.noAuth) {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
