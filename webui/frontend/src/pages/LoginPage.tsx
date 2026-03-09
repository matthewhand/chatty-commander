import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { Mic as MicIcon } from "lucide-react";

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
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
                autoFocus
                required
              />
            </div>

            <div className="form-control w-full">
              <label className="label" htmlFor="password">
                <span className="label-text">Password</span>
              </label>
              <input
                id="password"
                type="password"
                placeholder="Enter password"
                className="input input-bordered w-full input-primary"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="alert alert-error shadow-lg py-2" role="alert" aria-live="polite">
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className={`btn btn-primary w-full ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
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
