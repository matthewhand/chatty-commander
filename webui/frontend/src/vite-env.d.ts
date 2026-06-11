/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Truthy only in the static demo build (set via VITE_DEMO=1, see DEMO.md). */
  readonly VITE_DEMO?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
