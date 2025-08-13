const NON_ASCII = /[^\x00-\x7F]/g;

export function encodeASCII(s) {
  return s.replace(NON_ASCII, '?');
}

export function isASCII(s) {
  NON_ASCII.lastIndex = 0;
  return !NON_ASCII.test(s);
}

export function assertASCII(s) {
  if (!isASCII(s)) {
    throw new Error('Non-ASCII input');
  }
}
