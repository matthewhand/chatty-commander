export function encodeASCII(s) {
  return s.replace(/[^\x00-\x7F]/g, "?");
}
