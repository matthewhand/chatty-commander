// Encode a string into ASCII bytes, replacing non-ASCII chars with '?'
export function encodeASCII(str) {
  const out = new Uint8Array(str.length);
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    out[i] = code < 0x80 ? code : 0x3f; // '?'
  }
  return out;
}

// Decode ASCII bytes into a string, substituting non-ASCII bytes with '?'
export function decodeASCII(bytes) {
  let result = '';
  for (const b of bytes) {
    result += String.fromCharCode(b < 0x80 ? b : 0x3f);
  }
  return result;
}
