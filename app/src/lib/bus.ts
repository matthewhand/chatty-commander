export type BusHandler<T = any> = (payload: T, event: MessageEvent) => void;
export type AnyBusHandler = (
  type: string,
  payload: any,
  event: MessageEvent,
) => void;

export interface Bus {
  post: (type: string, payload?: any) => void;
  on: (type: string, handler: BusHandler) => () => void;
  onAny: (handler: AnyBusHandler) => () => void;
}

export function createBus(target: Window): Bus {
  const handlers = new Map<string, Set<BusHandler>>();
  const anyHandlers = new Set<AnyBusHandler>();
  let listening = false;

  const listener = (ev: MessageEvent) => {
    const msg = ev.data;
    if (!msg || typeof msg.type !== "string") return;
    const set = handlers.get(msg.type);
    if (set) set.forEach((h) => h(msg.payload, ev));
    anyHandlers.forEach((h) => h(msg.type, msg.payload, ev));
  };

  function ensureListener() {
    if (!listening && (handlers.size || anyHandlers.size)) {
      target.addEventListener("message", listener);
      listening = true;
    }
  }

  function cleanupListener() {
    if (listening && handlers.size === 0 && anyHandlers.size === 0) {
      target.removeEventListener("message", listener);
      listening = false;
    }
  }

  function post(type: string, payload?: any) {
    target.postMessage({ type, payload }, "*");
  }

  function on(type: string, handler: BusHandler) {
    let set = handlers.get(type);
    if (!set) {
      set = new Set();
      handlers.set(type, set);
    }
    set.add(handler);
    ensureListener();
    return () => {
      set!.delete(handler);
      if (set!.size === 0) {
        handlers.delete(type);
      }
      cleanupListener();
    };
  }

  function onAny(handler: AnyBusHandler) {
    anyHandlers.add(handler);
    ensureListener();
    return () => {
      anyHandlers.delete(handler);
      cleanupListener();
    };
  }

  return { post, on, onAny };
}