/**
 * Demo fixtures registry.
 *
 * Maps normalized API paths -> bundled static JSON captured from the
 * test-mode backend (see ../../DEMO.md for how to re-capture). These are the
 * canned GET responses the demo fetch shim serves. Only imported when
 * VITE_DEMO is truthy (the whole src/demo tree is dynamically imported behind
 * that guard in index.tsx, so it is tree-shaken out of the normal build).
 */

// Eagerly bundle every fixture JSON so they ship inside the static demo bundle
// with no runtime network access. `eager: true` inlines them at build time.
const modules = import.meta.glob("./fixtures/*.json", {
  eager: true,
  import: "default",
}) as Record<string, unknown>;

const byFile = (name: string): unknown => modules[`./fixtures/${name}`];

/**
 * Path -> fixture body. Keys are exact request paths (no query string) the SPA
 * issues. Keep in sync with the endpoints captured in DEMO.md.
 */
export const FIXTURES: Record<string, unknown> = {
  "/health": byFile("health.json"),
  "/api/v1/status": byFile("status.json"),
  "/api/v1/config": byFile("config.json"),
  "/api/v1/state": byFile("state.json"),
  "/api/v1/metrics": byFile("metrics.json"),
  "/api/v1/commands": byFile("commands.json"),
  "/api/audio/devices": byFile("audio_devices.json"),
  "/api/v1/audio/devices": byFile("v1_audio_devices.json"),
  "/api/themes": byFile("themes.json"),
  "/api/v1/dograh/status": byFile("dograh_status.json"),
  "/api/v1/dograh/call-state": byFile("dograh_call_state.json"),
  "/api/v1/dograh/workflows": byFile("dograh_workflows.json"),
  "/api/v1/advisors/context/stats": byFile("advisors_context_stats.json"),
  "/api/v1/advisors/personas": byFile("advisors_personas.json"),
};
