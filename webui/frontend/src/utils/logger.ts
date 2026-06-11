/**
 * Lightweight console wrapper that gates verbose logging behind the dev build.
 *
 * `debug`, `info`, and `warn` only emit when `import.meta.env.DEV` is true, so
 * connection chatter and retry notices stay out of production users' consoles.
 * `error` always logs — failures should never be silently swallowed.
 */

const isDev = (): boolean => {
  try {
    return Boolean(import.meta.env?.DEV);
  } catch {
    return false;
  }
};

export const logger = {
  debug: (...args: unknown[]): void => {
    if (isDev()) console.debug(...args);
  },
  info: (...args: unknown[]): void => {
    if (isDev()) console.info(...args);
  },
  warn: (...args: unknown[]): void => {
    if (isDev()) console.warn(...args);
  },
  error: (...args: unknown[]): void => {
    console.error(...args);
  },
};
