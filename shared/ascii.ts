const NON_ASCII = /[^\x00-\x7F]/g;

export function encodeASCII(s: string): string {
  return s.replace(NON_ASCII, "?");
}

export function decodeASCII(s: string): string {
  // Identity function - encoded ASCII is already valid string
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
