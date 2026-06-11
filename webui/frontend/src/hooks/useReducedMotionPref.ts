import { useReducedMotion } from 'framer-motion';

/**
 * Thin wrapper around framer-motion's `useReducedMotion` that returns a boolean
 * reflecting the user's `prefers-reduced-motion: reduce` setting.
 *
 * When `true`, entrance/stagger animations should be disabled: render the final
 * visual state immediately, with no transform/opacity transition and no
 * per-index delay. This keeps the rendered output identical while respecting
 * users who are sensitive to motion.
 *
 * framer-motion's hook can return `null` before it has resolved the media
 * query; we coerce that to `false` so callers always get a plain boolean.
 */
export function useReducedMotionPref(): boolean {
  return useReducedMotion() ?? false;
}
