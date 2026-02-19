import { build } from "../shared/esbuild.js";
import { promises as fs } from "fs";
import path from "path";
import crypto from "crypto";
import { fileURLToPath } from "url";
import { assertASCII, encodeASCII, decodeASCII } from "../shared/ascii.js";

/**
 * Build a browser bundle for a given entry file.
 * Returns the url where the bundle can be loaded along with
 * a version string and SHA256 checksum of the bundle contents.
 */
export async function buildCanvas(entry: string, asciiOnly = false) {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const root = path.resolve(__dirname, "..");
  const outDir = path.join(root, "build", "canvas");
  await fs.mkdir(outDir, { recursive: true });

  const absEntry = path.isAbsolute(entry) ? entry : path.join(root, entry);
  assertASCII(absEntry);
  const tmpOut = path.join(outDir, "bundle.js");

  let buildOptions: any = {
    entryPoints: [absEntry],
    bundle: true,
    platform: "browser" as const,
    format: "iife" as const,
    outfile: tmpOut,
    sourcemap: false,
  };

  if (asciiOnly) {
    // Add banner to disable storage APIs for ASCII-only mode
    const disable = `(() => {
  const apis = ['localStorage', 'sessionStorage', 'indexedDB'];
  for (const key of apis) {
    Object.defineProperty(globalThis, key, {
      get() { throw new Error('Storage disabled'); },
      configurable: true
    });
  }
})();`;

    buildOptions = {
      ...buildOptions,
      banner: {
        js: disable,
      },
    };
  }

  await build(buildOptions);

  const buf = await fs.readFile(tmpOut);

  // Apply ASCII filtering if requested
  let processedBuf = buf;
  if (asciiOnly) {
    const content = buf.toString();
    const asciiContent = decodeASCII(encodeASCII(content));
    processedBuf = Buffer.from(asciiContent);
  }

  const sha256 = crypto.createHash("sha256").update(processedBuf).digest("hex");
  const version = sha256.slice(0, 8);
  const finalName = `${version}.js`;
  await fs.rename(tmpOut, path.join(outDir, finalName));

  const bundleUrl = `/canvas/${finalName}`;
  return { bundleUrl, version, sha256 };
}
