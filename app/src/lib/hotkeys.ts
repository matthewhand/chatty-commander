import { useEffect } from "react";
import { useSettingsStore } from "../stores/settings";

function isMac() {
  return (
    typeof navigator !== "undefined" &&
    /Mac|iPod|iPhone|iPad/.test(navigator.platform)
  );
}

export function useGlobalHotkeys() {
  const reducedMotion = useSettingsStore((s) => s.reducedMotion);

  useEffect(() => {
    const focusPane = (id: string) => {
      const el = document.getElementById(id);
      if (el) {
        (el as HTMLElement).focus();
        el.scrollIntoView({
          behavior: reducedMotion ? "auto" : "smooth",
          block: "nearest",
          inline: "nearest",
        });
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if user is typing in input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      const isCtrl = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();

      // Ctrl/Cmd + 1: Focus chat
      if (isCtrl && key === "1") {
        event.preventDefault();
        focusPane("chat-pane");
        return;
      }

      // Ctrl/Cmd + 2: Focus canvas
      if (isCtrl && key === "2") {
        event.preventDefault();
        focusPane("canvas-pane");
        return;
      }

      // Ctrl/Cmd + 3: Focus sidecar
      if (isCtrl && key === "3") {
        event.preventDefault();
        focusPane("sidecar-pane");
        return;
      }

      // Ctrl/Cmd + `: Focus console (if available)
      if (isCtrl && key === "`") {
        event.preventDefault();
        const console = document.getElementById("console");
        if (console) {
          (console as HTMLElement).focus();
          console.scrollIntoView({
            behavior: reducedMotion ? "auto" : "smooth",
            block: "end",
            inline: "nearest",
          });
        }
        return;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [reducedMotion]);
}
