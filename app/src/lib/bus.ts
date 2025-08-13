export type BusHandler<T = any> = (data: T) => void;

// Registered listeners for postMessage events.
const listeners: Record<string, BusHandler[]> = {};

// Listen for messages from iframe or other windows.
window.addEventListener('message', evt => {
  const { type, payload } = (evt.data || {}) as { type?: string; payload?: any };
  if (!type) return;
  (listeners[type] || []).forEach(fn => fn(payload));
});

export function on<T = any>(type: string, handler: BusHandler<T>) {
  (listeners[type] ||= []).push(handler);
  return () => {
    listeners[type] = (listeners[type] || []).filter(h => h !== handler);
  };
}

export function post(win: Window | null | undefined, type: string, payload?: any) {
  win?.postMessage({ type, payload }, '*');
}
