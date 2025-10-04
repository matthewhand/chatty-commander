type EventHandler<T = any> = (data: T) => void;
type AnyHandler = (type: string, payload: any, event?: Event) => void;

interface Bus {
  post: <T>(type: string, payload: T) => void;
  on: <T>(type: string, handler: EventHandler<T>) => () => void;
  onAny: (handler: AnyHandler) => () => void;
}

export function createBus(): Bus {
  const handlers = new Map<string, Set<EventHandler>>();
  const anyHandlers: Set<AnyHandler> = new Set();

  const post = <T>(type: string, payload: T) => {
    const hs = handlers.get(type);
    if (hs) {
      hs.forEach((h) => h(payload));
    }
    anyHandlers.forEach((h) => h(type, payload));
  };

  const on = <T>(type: string, handler: EventHandler<T>) => {
    let hs = handlers.get(type);
    if (!hs) {
      hs = new Set();
      handlers.set(type, hs);
    }
    hs.add(handler);
    return () => hs.delete(handler);
  };

  const onAny = (handler: AnyHandler) => {
    anyHandlers.add(handler);
    return () => anyHandlers.delete(handler);
  };

  return { post, on, onAny };
}
