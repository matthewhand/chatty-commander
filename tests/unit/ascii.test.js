import test from 'node:test';
import assert from 'node:assert';
import { encodeASCII, decodeASCII } from '../../app/src/lib/ascii.js';

test('ASCII encode/decode replaces non-ascii', () => {
  const encodedHello = encodeASCII('hello');
  assert.strictEqual(decodeASCII(encodedHello), 'hello');

  const encoded = encodeASCII('hi✓');
  assert.deepStrictEqual(Array.from(encoded), [0x68, 0x69, 0x3f]);
  assert.strictEqual(decodeASCII(encoded), 'hi?');
});
