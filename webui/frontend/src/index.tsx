import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

const container = document.getElementById("root");
const root = createRoot(container!);

async function bootstrap() {
  // Static demo mode (opt-in, build-time flag VITE_DEMO). The entire demo
  // runtime is dynamically imported behind this guard so it is tree-shaken out
  // of the normal production bundle — when VITE_DEMO is unset, none of these
  // modules are referenced and behavior is byte-for-byte the standard app.
  let DemoBanner: React.ComponentType | null = null;
  if (import.meta.env.VITE_DEMO) {
    const [{ installDemoMocks }, banner] = await Promise.all([
      import("./demo/installDemoMocks"),
      import("./demo/DemoBanner"),
    ]);
    // Install fetch + WebSocket shims BEFORE the app renders so the very first
    // requests/sockets are served from fixtures.
    installDemoMocks();
    DemoBanner = banner.default;
  }

  root.render(
    <React.StrictMode>
      {DemoBanner ? <DemoBanner /> : null}
      <App />
    </React.StrictMode>
  );
}

void bootstrap();
