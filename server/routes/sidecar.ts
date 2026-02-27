import { Router } from "express";
import { readFile } from "fs/promises";
import { execFile as execFileCb } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";
import { createHmac } from "crypto";

const execFile = promisify(execFileCb);
const router = Router();
const SECRET = process.env.SIDECAR_SECRET || "dev-secret";

// Helper to ensure path is within project root
function isSafePath(filePath: string): boolean {
  const resolved = path.resolve(filePath);
  const cwd = process.cwd();
  return resolved.startsWith(cwd);
}

// Enhanced signature with expiry (default 5 mins)
function sign(p: string, expiry: number) {
  const data = `${p}:${expiry}`;
  return createHmac("sha256", SECRET).update(data).digest("hex");
}

// Generate a signed URL for the requested file. The returned URL can be used
// to fetch the file contents via `/api/sidecar/file/content`.
router.get("/file", async (req, res) => {
  const filePath = req.query.path as string;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  // 1. Strict Path Scoping
  if (!isSafePath(filePath)) {
    res.status(403).json({ error: "access denied: path outside project root" });
    return;
  }

  const isDiff = req.query.diff === "1" || req.query.diff === "true";
  const ignoreWhitespace = req.query.ignoreWhitespace === "1" || req.query.ignoreWhitespace === "true";

  try {
    if (isDiff) {
      // 4. Configurable Diff Options
      const args = ["diff", "HEAD"];
      if (ignoreWhitespace) {
        args.push("-w");
      }
      args.push("--", filePath);

      const { stdout } = await execFile("git", args);
      res.json({ content: stdout });
    } else {
      // For file requests, generate a signed URL
      const abs = path.resolve(filePath);
      if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
        res.status(404).json({ error: "not found" });
        return;
      }

      // 2. Time-Limited Signatures
      const expiry = Date.now() + 5 * 60 * 1000; // 5 minutes from now
      const signature = sign(abs, expiry);
      const url = `/api/sidecar/file/content?path=${encodeURIComponent(abs)}&sig=${signature}&expiry=${expiry}`;
      res.json({ url });
    }
  } catch (err) {
    res.status(404).json({ error: "file not found" });
  }
});

// 3. Git Blame Endpoint
router.get("/blame", async (req, res) => {
  const filePath = req.query.path as string;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  if (!isSafePath(filePath)) {
    res.status(403).json({ error: "access denied: path outside project root" });
    return;
  }

  try {
    const { stdout } = await execFile("git", ["blame", "--line-porcelain", "--", filePath]);
    res.json({ content: stdout });
  } catch (err) {
    res.status(500).json({ error: "failed to retrieve blame info" });
  }
});

// 4. Git Hygiene Check
router.get("/git/check", async (req, res) => {
  const filePath = req.query.path as string;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  if (!isSafePath(filePath)) {
    res.status(403).json({ error: "access denied: path outside project root" });
    return;
  }

  try {
    // "git diff --check" exits with non-zero if issues found
    await execFile("git", ["diff", "--check", "HEAD", "--", filePath]);
    res.json({ status: "clean" });
  } catch (err: any) {
    // If it's an exit code issue, it means whitespace errors found
    if (err.code && err.code !== 0) {
      res.json({ status: "issues_found", output: err.stdout });
    } else {
      res.status(500).json({ error: "git check failed" });
    }
  }
});

// 5. Interactive Git Staging (Apply Patch)
router.post("/git/apply", async (req, res) => {
  const patch = req.body.patch;

  if (typeof patch !== "string" || !patch) {
    res.status(400).json({ error: "patch content required" });
    return;
  }

  try {
    // Write patch to temp file or pipe it to stdin?
    // Using stdin is safer and cleaner.
    const child = execFileCb("git", ["apply", "--cached", "-"], (error, stdout, stderr) => {
      if (error) {
        res.status(400).json({ error: "failed to apply patch", stderr });
      } else {
        res.json({ status: "success", message: "patch applied to index" });
      }
    });

    if (child.stdin) {
        child.stdin.write(patch);
        child.stdin.end();
    } else {
        res.status(500).json({ error: "failed to open stdin" });
    }

  } catch (err) {
    res.status(500).json({ error: "internal error" });
  }
});

// 6. Safe File Restoration
router.post("/file/restore", async (req, res) => {
  const filePath = req.body.path;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  if (!isSafePath(filePath)) {
    res.status(403).json({ error: "access denied: path outside project root" });
    return;
  }

  try {
    // Revert changes to file (checkout HEAD)
    await execFile("git", ["checkout", "HEAD", "--", filePath]);
    res.json({ status: "restored", message: `Reverted changes to ${filePath}` });
  } catch (err) {
    res.status(500).json({ error: "failed to restore file" });
  }
});

// 7. Repository Health/Stats
router.get("/repo/status", async (req, res) => {
  try {
    const branch = (await execFile("git", ["rev-parse", "--abbrev-ref", "HEAD"])).stdout.trim();
    const statusOutput = (await execFile("git", ["status", "--porcelain"])).stdout;
    const modifiedCount = statusOutput.split("\n").filter(l => l.trim().length > 0).length;

    // Check ahead/behind
    // This requires upstream to be set. If not, it might fail or return empty.
    let ahead = 0;
    let behind = 0;
    try {
        const trackInfo = (await execFile("git", ["rev-list", "--left-right", "--count", "HEAD...@{u}"])).stdout.trim();
        const parts = trackInfo.split(/\s+/);
        if (parts.length === 2) {
            ahead = parseInt(parts[0], 10);
            behind = parseInt(parts[1], 10);
        }
    } catch (e) {
        // Upstream might not be configured
    }

    res.json({
        branch,
        modifiedFiles: modifiedCount,
        ahead,
        behind
    });
  } catch (err) {
    res.status(500).json({ error: "failed to get repo status" });
  }
});

// Serve file contents after verifying the signature.
router.get("/file/content", (req, res) => {
  const file = req.query.path as string;
  const sig = req.query.sig as string;
  const expiryStr = req.query.expiry as string;

  if (!file || !sig || !expiryStr) {
    res.status(400).end();
    return;
  }

  const expiry = parseInt(expiryStr, 10);
  if (isNaN(expiry)) {
    res.status(400).end();
    return;
  }

  if (Date.now() > expiry) {
    res.status(403).send("URL expired");
    return;
  }

  const abs = path.resolve(file);

  // Verify strict path scoping again just in case
  if (!isSafePath(abs)) {
     res.status(403).end();
     return;
  }

  if (sig !== sign(abs, expiry)) {
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
