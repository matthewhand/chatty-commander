import path from 'path';
import { fileURLToPath } from 'url';
import { buildCanvas } from '../../workers/canvas-builder.js';

export async function build(entry: string, asciiOnly?: boolean) {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const root = path.resolve(__dirname, '..', '..');
  const absEntry = path.isAbsolute(entry) ? entry : path.join(root, entry);
  return await buildCanvas(absEntry);
}
