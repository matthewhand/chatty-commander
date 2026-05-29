import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { Mic as MicIcon, Eye as EyeIcon, EyeOff as EyeOffIcon } from "lucide-react";

const LoginPage: React.FC = () => {
  useEffect(() => {
    document.title = "Login | ChattyCommander";
  }, []);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const { login } = useAuth();

  const validateUsername = (value: string) => {
    if (!value.trim()) {
      setUsernameError("Username is required");
      return false;
    }
    if (value.length < 3) {
      setUsernameError("Username must be at least 3 characters");
      return false;
    }
    setUsernameError("");
    return true;
  };

  const validatePassword = (value: string) => {
    if (!value) {
      setPasswordError("Password is required");
      return false;
    }
    if (value.length < 6) {
      setPasswordError("Password must be at least 6 characters");
      return false;
    }
    setPasswordError("");
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    const isUsernameValid = validateUsername(username);
    const isPasswordValid = validatePassword(password);
    
    if (!isUsernameValid || !isPasswordValid) {
      return;
    }
    
    setLoading(true);
    const success = await login(username, password);
    setLoading(false);
    if (!success) {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-300 pattern-isometric">
      <div className="card w-96 bg-base-100 shadow-xl border border-primary/20">
        <div className="card-body items-center text-center">
          <div className="avatar placeholder mb-4">
            <div className="bg-primary text-primary-content rounded-full w-20 ring ring-primary ring-offset-2 ring-offset-base-100">
              <MicIcon size={48} />
            </div>
          </div>
          <h2 className="card-title text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Chatty Commander
          </h2>
          <p className="text-sm opacity-70 mb-4">Voice Control System</p>

          <form onSubmit={handleSubmit} className="w-full space-y-4">
            <div className="form-control w-full">
              <label className="label cursor-pointer" htmlFor="username">
                <span className="label-text">Username</span>
              </label>
              <input
                id="username"
                type="text"
                placeholder="Enter username"
                className={`input input-bordered w-full input-primary ${usernameError ? 'input-error' : ''}`}
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  validateUsername(e.target.value);
                }}
                onBlur={(e) => validateUsername(e.target.value)}
                autoFocus
                required
                aria-invalid={!!usernameError}
                aria-describedby={usernameError ? "username-error" : undefined}
              />
              {usernameError && (
                <span id="username-error" className="text-error text-xs mt-1">{usernameError}</span>
              )}
            </div>

            <div className="form-control w-full">
              <label className="label cursor-pointer" htmlFor="password">
                <span className="label-text">Password</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password"
                  className={`input input-bordered w-full input-primary pr-12 ${passwordError ? 'input-error' : ''}`}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    validatePassword(e.target.value);
                  }}
                  onBlur={(e) => validatePassword(e.target.value)}
                  required
                  aria-invalid={!!passwordError}
                  aria-describedby={passwordError ? "password-error" : undefined}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-base-content/50 hover:text-base-content"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOffIcon size={18} /> : <EyeIcon size={18} />}
                </button>
              </div>
              {passwordError && (
                <span id="password-error" className="text-error text-xs mt-1">{passwordError}</span>
              )}
            </div>

            <div className="form-control">
              <label className="label cursor-pointer justify-start gap-3">
                <input
                  type="checkbox"
                  className="checkbox checkbox-primary checkbox-sm"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span className="label-text">Remember me</span>
              </label>
            </div>

            {error && (
              <div className="alert alert-error shadow-lg py-2">
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
            >
              {loading && <span className="loading loading-spinner"></span>}
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>

          <div className="divider"></div>

          <div className="alert alert-info shadow-sm text-left text-xs">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
              <span>Auth configured via CLI. No reset function.</span>
              <br />
              <span className="opacity-75">Use --no-auth to disable.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
