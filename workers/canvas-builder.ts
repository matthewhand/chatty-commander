import { encodeASCII, decodeASCII } from '../app/src/lib/ascii.js';

export async function buildCanvas(entry: string, asciiOnly = false) {
  let code = entry;
  if (asciiOnly) {
    // Strip non-ASCII characters
    code = decodeASCII(encodeASCII(code));

    // Disable storage related APIs
    const disable = `(() => {\n` +
      `  const apis = ['localStorage', 'sessionStorage', 'indexedDB'];\n` +
      `  for (const key of apis) {\n` +
      `    Object.defineProperty(globalThis, key, {\n` +
      `      get() { throw new Error('Storage disabled'); },\n` +
      `      configurable: true\n` +
      `    });\n` +
      `  }\n` +
      `})();\n`;
    code = disable + code;
  }

  // placeholder build output with processed code
  return { bundleUrl: '/bundle.js', version: '0.0.0', sha256: '', code };
}
