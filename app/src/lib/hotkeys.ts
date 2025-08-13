import { useEffect } from 'react';
import { useSettingsStore } from '../stores/settings';

function isMac() {
  return typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
}

export function useGlobalHotkeys() {
  const reducedMotion = useSettingsStore(s => s.reducedMotion);

  useEffect(() => {
    const focusPane = (id: string) => {
      const el = document.getElementById(id);
      if (el) {
        (el as HTMLElement).focus();
        el.scrollIntoView({
          behavior: reducedMotion ? 'auto' : 'smooth',
          block: 'nearest',
          inline: 'nearest',
        });
      }
    };

    const handler = (e: KeyboardEvent) => {
      const meta = isMac() ? e.metaKey : e.ctrlKey;
      const key = e.key;

      if (meta && key.toLowerCase() === 'k') {
        e.preventDefault();
        (document.getElementById('chat-input') as HTMLElement | null)?.focus();
      } else if (meta && key === 'Enter') {
        e.preventDefault();
        window.dispatchEvent(new Event('chat:send'));
      } else if (e.altKey && ['1', '2', '3'].includes(key)) {
        e.preventDefault();
        if (key === '1') focusPane('chat-pane');
        if (key === '2') focusPane('canvas-pane');
        if (key === '3') focusPane('review-pane');
      } else if (key === '`') {
        e.preventDefault();
        focusPane('console-pane');
      } else if (key === 'F1') {
        e.preventDefault();
        window.open('/docs', '_blank');
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [reducedMotion]);
}
