import { build } from 'esbuild';
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { assertASCII } from '@shared/ascii';

/**
 * Build a browser bundle for a given entry file.
 * Returns the url where the bundle can be loaded along with
 * a version string and SHA256 checksum of the bundle contents.
 */
export async function buildCanvas(entry: string) {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const root = path.resolve(__dirname, '..');
  const outDir = path.join(root, 'build', 'canvas');
  await fs.mkdir(outDir, { recursive: true });

  const absEntry = path.isAbsolute(entry) ? entry : path.join(root, entry);
  assertASCII(absEntry);
  const tmpOut = path.join(outDir, 'bundle.js');

  await build({
    entryPoints: [absEntry],
    bundle: true,
    platform: 'browser',
    format: 'iife',
    outfile: tmpOut,
    sourcemap: false
  });

  const buf = await fs.readFile(tmpOut);
  const sha256 = crypto.createHash('sha256').update(buf).digest('hex');
  const version = sha256.slice(0, 8);
  const finalName = `${version}.js`;
  await fs.rename(tmpOut, path.join(outDir, finalName));

  const bundleUrl = `/canvas/${finalName}`;
  return { bundleUrl, version, sha256 };
}
