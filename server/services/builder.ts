import { readFile, writeFile } from 'node:fs/promises';
import { encodeASCII } from '../../app/src/lib/ascii.js';

export async function build(entry: string, asciiOnly?: boolean) {
  let contents = await readFile(entry, 'utf8');
  if (asciiOnly) {
    contents = encodeASCII(contents);
  }
  await writeFile('/tmp/bundle.js', contents, 'utf8');
  return { bundleUrl: '/bundle.js', version: '0.0.0', sha256: '' };
}
