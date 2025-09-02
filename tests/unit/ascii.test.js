import test from "node:test";
import assert from "node:assert";
import { encodeASCII, isASCII } from "../../shared/ascii.mjs";

test("encodeASCII replaces non-ascii", () => {
  assert.strictEqual(encodeASCII("hello"), "hello");
  assert.strictEqual(encodeASCII("hi✓"), "hi?");
});

test("isASCII guards strings", () => {
  assert.ok(isASCII("plain"));
  assert.ok(!isASCII("✓"));
});
