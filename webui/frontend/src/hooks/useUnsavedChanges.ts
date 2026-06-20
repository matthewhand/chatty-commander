import { useEffect } from "react";

/**
 * Tracks, across the whole app, whether *any* mounted form currently has unsaved
 * edits. This is intentionally a module-level registry (not React state): the
 * code that needs to *read* "is anything dirty?" lives in the session-expiry
 * path inside the auth layer (`useAuth`), which sits at a different point in the
 * provider tree than the forms that are dirty. A plain registry lets a form
 * advertise its dirtiness without prop-drilling a flag up to the auth provider.
 *
 * Each registration is an opaque token (a fresh object) so two forms that are
 * both dirty don't collide — membership is by identity, and the set is empty
 * exactly when nothing is dirty.
 */
const dirtyRegistrations = new Set<object>();

type Subscriber = () => void;
const subscribers = new Set<Subscriber>();

function notify(): void {
  for (const subscriber of subscribers) {
    try {
      subscriber();
    } catch {
      /* a misbehaving subscriber must not block the others */
    }
  }
}

/**
 * Whether any currently-mounted form has registered itself as dirty. Read from
 * the session-expiry path to decide whether to defer the forced sign-out so the
 * user's in-progress edits survive on the page.
 */
export function hasUnsavedChanges(): boolean {
  return dirtyRegistrations.size > 0;
}

/**
 * Subscribe to changes in the global "anything dirty?" state. Returns an
 * unsubscribe function. Useful for components that want to render reactively off
 * {@link hasUnsavedChanges} rather than poll it.
 */
export function subscribeUnsavedChanges(subscriber: Subscriber): () => void {
  subscribers.add(subscriber);
  return () => {
    subscribers.delete(subscriber);
  };
}

/**
 * Test-only escape hatch to clear the registry between tests so module-level
 * state doesn't leak across cases. Not used in app code.
 */
export function __resetUnsavedChanges(): void {
  dirtyRegistrations.clear();
  notify();
}

/**
 * Register this component as having unsaved changes while `dirty` is true.
 *
 * The registration is added when `dirty` becomes true and removed when it
 * becomes false again or the component unmounts (whichever comes first), so the
 * global {@link hasUnsavedChanges} flag always reflects what's actually on
 * screen. SSR-safe: the registry is a plain JS Set with no DOM/`window` access.
 */
export function useUnsavedChanges(dirty: boolean): void {
  useEffect(() => {
    if (!dirty) return;
    // A unique token per active registration so concurrent dirty forms coexist.
    const token = {};
    dirtyRegistrations.add(token);
    notify();
    return () => {
      dirtyRegistrations.delete(token);
      notify();
    };
  }, [dirty]);
}
