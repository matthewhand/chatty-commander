import test from 'node:test';
import assert from 'node:assert';
import { encodeASCII } from '../../app/src/lib/ascii.js';

test('encodeASCII replaces non-ascii', () => {
  assert.strictEqual(encodeASCII('hello'), 'hello');
  assert.strictEqual(encodeASCII('hi✓'), 'hi?');
});
