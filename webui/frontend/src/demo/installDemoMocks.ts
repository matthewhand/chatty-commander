/**
 * installDemoMocks — wires up the fully-static demo runtime.
 *
 *  1. Monkeypatches window.fetch to resolve /api and /health requests from the
 *     bundled fixtures (../demo/fixtures). Unrecorded GETs fall back to a clear
 *     console.warn + 200 {}; POST/PUT/DELETE return a friendly canned ok so the
 *     UI's optimistic flows (command execute, config save) don't error.
 *  2. Replaces window.WebSocket with FakeWebSocket so the dashboard reports
 *     "Connected" and shows live telemetry without any backend.
 *
 * Everything here is only loaded behind `if (import.meta.env.VITE_DEMO)` in
 * index.tsx, via dynamic import, so the normal production bundle never includes
 * it. No network access ever occurs in demo mode.
 */

import { FIXTURES } from "./fixtures";
import { FakeWebSocket } from "./FakeWebSocket";

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

/** Extract just the pathname from any same-origin or relative request. */
function pathOf(input: RequestInfo | URL): string {
  let raw: string;
  if (typeof input === "string") raw = input;
  else if (input instanceof URL) raw = input.toString();
  else if (input instanceof Request) raw = input.url;
  else raw = String(input);
  try {
    // Resolve relative paths against the current origin.
    return new URL(raw, window.location.origin).pathname;
  } catch {
    // Strip any query string as a last resort.
    return raw.split("?")[0];
  }
}

function methodOf(input: RequestInfo | URL, init?: RequestInit): string {
  if (init?.method) return init.method.toUpperCase();
  if (input instanceof Request && input.method) return input.method.toUpperCase();
  return "GET";
}

export function installDemoMocks(): void {
  const realFetch = window.fetch?.bind(window);

  window.fetch = async (
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> => {
    const path = pathOf(input);
    const method = methodOf(input, init);

    // Only intercept the app's own API surface. Anything else (should be
    // nothing in a static build) falls through to the real fetch if present.
    const isApi = path === "/health" || path.startsWith("/api/");
    if (!isApi) {
      if (realFetch) return realFetch(input as any, init);
      return jsonResponse({}, 200);
    }

    if (method === "GET") {
      if (path in FIXTURES) {
        return jsonResponse(FIXTURES[path]);
      }
      // eslint-disable-next-line no-console
      console.warn(
        `[demo] No fixture for GET ${path} — returning empty {}. ` +
          `Capture it (see DEMO.md) to populate this view.`
      );
      return jsonResponse({});
    }

    // Mutating requests: pretend it worked. Keeps optimistic UI happy.
    // eslint-disable-next-line no-console
    console.info(`[demo] ${method} ${path} — canned ok (no backend in demo mode).`);
    return jsonResponse({ status: "ok", demo: true });
  };

  // Replace the global WebSocket with the never-connecting fake.
  (window as any).WebSocket = FakeWebSocket as unknown as typeof WebSocket;
}

export default installDemoMocks;
