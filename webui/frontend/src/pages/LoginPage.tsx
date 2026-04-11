import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { Mic as MicIcon } from "lucide-react";
import { Button, Card, Input, Alert, Avatar, Checkbox } from "../components/DaisyUI";

const LoginPage: React.FC = () => {
  useEffect(() => {
    document.title = "Login | ChattyCommander";
  }, []);

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
      <Card className="w-96 shadow-xl border border-primary/20">
        <div className="items-center text-center">
          <Avatar placeholder shape="circle" size="xl" className="mb-4" innerClassName="bg-primary text-primary-content ring ring-primary ring-offset-2 ring-offset-base-100">
            <MicIcon size={48} />
          </Avatar>
          <h2 className="card-title text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent justify-center">
            Chatty Commander
          </h2>
          <p className="text-sm opacity-70 mb-4">Voice Control System</p>

          <form onSubmit={handleSubmit} className="w-full space-y-4">
            <Input
              id="username"
              type="text"
              placeholder="Enter username"
              variant="primary"
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />

            <Input
              id="password"
              type="password"
              placeholder="Enter password"
              variant="primary"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <div className="flex items-center justify-between text-sm w-full px-1">
              <Checkbox label="Remember me" size="sm" variant="primary" />
              <button type="button" className="link link-hover text-base-content/60 bg-transparent border-0 p-0 cursor-pointer" onClick={(e) => e.preventDefault()}>Forgot password?</button>
            </div>

            {error && (
              <Alert variant="error" className="shadow-lg py-2">
                <span>{error}</span>
              </Alert>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
              loadingText="Logging in..."
            >
              Login
            </Button>
          </form>

          <div className="divider"></div>

          <Alert
            variant="info"
            className="shadow-sm text-left text-xs"
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            }
          >
            <div>
              <span>Auth configured via CLI. No reset function.</span>
              <br />
              <span className="opacity-75">Use --no-auth to disable.</span>
            </div>
          </Alert>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
