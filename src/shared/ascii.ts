const NON_ASCII = /[^\x00-\x7F]/g;

export function encodeASCII(s: string): Uint8Array {
  const bytes = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    bytes[i] = code > 127 ? 63 : code; // 63 is '?'
  }
  return bytes;
}

export function decodeASCII(bytes: Uint8Array): string {
  let s = "";
  for (let i = 0; i < bytes.length; i++) {
    const code = bytes[i];
    s += String.fromCharCode(code > 127 ? 63 : code); // '?' for non-ASCII
  }
  return s;
}

export function isASCII(s: string): boolean {
  NON_ASCII.lastIndex = 0;
  return !NON_ASCII.test(s);
}

export function assertASCII(s: string): void {
  if (!isASCII(s)) {
    throw new Error("Non-ASCII input");
  }
}
