import { Router } from "express";
import { readFile } from "fs/promises";
import { exec as execCb } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";
import { createHmac } from "crypto";

const exec = promisify(execCb);
const router = Router();
const SECRET = process.env.SIDECAR_SECRET || "dev-secret";

// Define the project root as the current working directory
// This prevents access to files outside the intended scope (e.g. /etc/passwd)
const PROJECT_ROOT = path.resolve(process.cwd());

function isSafePath(p: string) {
  const abs = path.resolve(p);
  // Check if the resolved path starts with the project root
  return abs.startsWith(PROJECT_ROOT + path.sep) || abs === PROJECT_ROOT;
}

function sign(p: string) {
  return createHmac("sha256", SECRET).update(p).digest("hex");
}

// Generate a signed URL for the requested file. The returned URL can be used
// to fetch the file contents via `/api/sidecar/file/content`.
router.get("/file", async (req, res) => {
  const filePath = req.query.path;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  const isDiff = req.query.diff === "1" || req.query.diff === "true";

  try {
    // Validate path is safe before proceeding
    if (!isSafePath(filePath)) {
      res.status(403).json({ error: "access denied" });
      return;
    }

    if (isDiff) {
      // For diff requests, return the diff content directly
      const { stdout } = await exec(`git diff HEAD -- ${filePath}`);
      res.json({ content: stdout });
    } else {
      // For file requests, generate a signed URL
      const abs = path.resolve(filePath);
      if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
        res.status(404).json({ error: "not found" });
        return;
      }

      const url = `/api/sidecar/file/content?path=${encodeURIComponent(abs)}&sig=${sign(abs)}`;
      res.json({ url });
    }
  } catch (err) {
    res.status(404).json({ error: "file not found" });
  }
});

// Serve file contents after verifying the signature.
router.get("/file/content", (req, res) => {
  const file = req.query.path as string;
  const sig = req.query.sig as string;
  if (!file || !sig) {
    res.status(400).end();
    return;
  }

  const abs = path.resolve(file);

  if (!isSafePath(abs)) {
    res.status(403).end();
    return;
  }

  if (sig !== sign(abs)) {
    res.status(403).end();
    return;
  }

  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
    res.status(404).end();
    return;
  }

  res.sendFile(abs);
});

export default router;
