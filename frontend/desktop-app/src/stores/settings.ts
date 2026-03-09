import { create } from "zustand";

interface SettingsStore {
  theme: "dark";
  reducedMotion: boolean;
  telemetryOptIn: boolean;
}

export const useSettingsStore = create<SettingsStore>(() => ({
  theme: "dark",
  reducedMotion: false,
  telemetryOptIn: false,
}));
