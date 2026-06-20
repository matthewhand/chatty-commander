import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../hooks/useAuth";
import { authService } from "../services/authService";
import { Check, Eye, EyeOff } from "lucide-react";
import Logo from "../components/Logo";

// Brand-panel highlights shown beside the form on desktop. Kept accurate to the
// product (local-first voice assistant: wake words -> actions).
const LOGIN_HIGHLIGHTS = [
  "Wake words trigger keypresses, URLs, scripts & calls",
  "Local-first — your audio stays on your machine",
  "Live dashboard, voice test & AI command authoring",
];

const LoginPage: React.FC = () => {
  useEffect(() => {
    document.title = "Login | ChattyCommander";
  }, []);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login, sessionExpiredNotice, clearSessionExpiredNotice } = useAuth();
  const passwordRef = useRef<HTMLInputElement>(null);

  // After a failed login the password input is briefly disabled (loading), so
  // we can't focus it synchronously inside the handler — the DOM hasn't
  // re-enabled it yet. Defer focus to an effect that runs once the error is
  // shown and the field is interactive again.
  useEffect(() => {
    if (error && !loading) {
      passwordRef.current?.focus();
    }
  }, [error, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    // Starting a fresh sign-in supersedes any stale "session expired" notice
    // that redirected the user here.
    clearSessionExpiredNotice();
    setLoading(true);
    const success = await login(username, password);
    setLoading(false);
    if (!success) {
      // The useAuth hook only returns a boolean, so recover the reason from the
      // service to show actionable copy instead of one generic message.
      const message =
        authService.lastLoginErrorKind === "network"
          ? "Can't reach the server. Please try again."
          : "Invalid username or password";
      setError(message);
      // Clear the password so a screen-reader user (and everyone else) can
      // immediately retry; focus returns to it via the effect above.
      setPassword("");
    }
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-base-300 via-base-200 to-base-300">
      {/* Branded hero panel — desktop only. Fills the space a lone centered
          card would leave empty and tells a first-time user what the product
          does before they sign in. Hidden below lg, where the form stacks. */}
      <aside className="hidden lg:flex lg:w-[44%] flex-col justify-center gap-8 px-12 xl:px-20 border-r border-base-content/10">
        <Logo size={44} className="text-4xl" />
        <div>
          <h1 className="text-3xl xl:text-4xl font-bold text-gradient-primary leading-tight">
            Turn your voice into action
          </h1>
          <p className="mt-3 text-base-content/70 max-w-md">
            ChattyCommander is a local-first voice assistant that maps wake words
            to the things you actually do on your machine.
          </p>
        </div>
        <ul className="space-y-3">
          {LOGIN_HIGHLIGHTS.map((item) => (
            <li key={item} className="flex items-start gap-3 text-base-content/80">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                <Check size={13} strokeWidth={3} aria-hidden="true" />
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </aside>

      {/* Form panel — full width on mobile, the right column on desktop. */}
      <div className="flex-1 flex items-center justify-center p-6">
      <div className="card w-96 bg-base-100 shadow-xl border border-primary/20">
        <div className="card-body items-center text-center">
          {/* The hero panel carries the brand on desktop, so only show the
              lockup here on smaller screens where the panel is hidden. */}
          <Logo size={36} className="text-3xl mt-2 mb-1 lg:hidden" />
          <p className="text-sm opacity-70 mb-4 lg:hidden">Voice Control System</p>

          {sessionExpiredNotice && (
            <div
              role="status"
              aria-live="polite"
              className="alert alert-warning shadow-sm w-full text-left text-sm mb-4"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                className="stroke-current shrink-0 h-6 w-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>{sessionExpiredNotice}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="w-full space-y-4">
            <div className="form-control w-full">
              <label className="label" htmlFor="username">
                <span className="label-text">Username</span>
              </label>
              <input
                id="username"
                type="text"
                placeholder="Enter username"
                className="input input-bordered w-full input-primary"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                required
                disabled={loading}
                aria-invalid={!!error}
                aria-describedby={error ? "login-error" : undefined}
              />
            </div>

            <div className="form-control w-full">
              <label className="label" htmlFor="password">
                <span className="label-text">Password</span>
              </label>
              <div className="relative w-full">
                <input
                  id="password"
                  ref={passwordRef}
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password"
                  className="input input-bordered w-full input-primary pr-12"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  disabled={loading}
                  aria-invalid={!!error}
                  aria-describedby={error ? "login-error" : undefined}
                />
                <button
                  type="button"
                  className="btn btn-ghost btn-sm btn-circle absolute right-1 top-1/2 -translate-y-1/2"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                  disabled={loading}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div
                id="login-error"
                role="alert"
                aria-live="assertive"
                className="alert alert-error shadow-lg py-2"
              >
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
              aria-busy={loading}
            >
              {loading && <span className="loading loading-spinner"></span>}
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>

          <div className="divider"></div>

          <div className="alert alert-info shadow-sm text-left text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <span>Credentials are managed by your administrator.</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};

export default LoginPage;
