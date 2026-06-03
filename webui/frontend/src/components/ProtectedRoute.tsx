import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

type ProtectedRouteProps = {
  children: React.ReactNode;
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();

  // Allow bypassing auth in development/no-auth mode based on dynamic backend configuration.
  // This is only ever set when the backend itself reports auth is disabled; log it so the
  // bypass is auditable rather than silent.
  if (user?.noAuth) {
    console.warn("ProtectedRoute: serving protected route without auth (backend no-auth mode)");
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
