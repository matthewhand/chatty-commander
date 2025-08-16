export function encodeASCII(s: string): string {
  return s.replace(/[^\x00-\x7F]/g, '?');
}
