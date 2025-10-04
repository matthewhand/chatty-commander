import test from "node:test";
import assert from "node:assert";
import { encodeASCII, decodeASCII, isASCII } from "../../shared/ascii.ts";

test("encodeASCII returns Uint8Array and replaces non-ascii", () => {
  const hello = encodeASCII("hello");
  assert.ok(hello instanceof Uint8Array);
  assert.strictEqual(Array.from(hello).join(","), "104,101,108,108,111");

  const hiCheck = encodeASCII("hi✓");
  assert.ok(hiCheck instanceof Uint8Array);
  assert.strictEqual(Array.from(hiCheck).join(","), "104,105,63");
});

test("decodeASCII converts Uint8Array back to string", () => {
  const bytes = new Uint8Array([104, 101, 108, 108, 111]);
  assert.strictEqual(decodeASCII(bytes), "hello");

  const nonAsciiBytes = new Uint8Array([104, 105, 200]);
  assert.strictEqual(decodeASCII(nonAsciiBytes), "hi?");
});

test("encode/decode roundtrip preserves ASCII content", () => {
  const original = "hello world";
  const encoded = encodeASCII(original);
  const decoded = decodeASCII(encoded);
  assert.strictEqual(decoded, original);
});

test("encode/decode roundtrip replaces non-ASCII with ?", () => {
  const original = "hi✓";
  const encoded = encodeASCII(original);
  const decoded = decodeASCII(encoded);
  assert.strictEqual(decoded, "hi?");
});

test("isASCII guards strings", () => {
  assert.ok(isASCII("plain"));
  assert.ok(!isASCII("✓"));
});
