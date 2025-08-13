import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import { createHmac } from 'crypto';

const router = Router();
const SECRET = process.env.SIDECAR_SECRET || 'dev-secret';

function sign(p: string) {
  return createHmac('sha256', SECRET).update(p).digest('hex');
}

// Generate a signed URL for the requested file. The returned URL can be used
// to fetch the file contents via `/api/sidecar/file/content`.
router.get('/file', (req, res) => {
  const file = req.query.path as string;
  if (!file) {
    res.status(400).json({ error: 'path required' });
    return;
  }

  const abs = path.resolve(file);
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
    res.status(404).json({ error: 'not found' });
    return;
  }

  const url = `/api/sidecar/file/content?path=${encodeURIComponent(abs)}&sig=${sign(abs)}`;
  res.json({ url });
});

// Serve file contents after verifying the signature.
router.get('/file/content', (req, res) => {
  const file = req.query.path as string;
  const sig = req.query.sig as string;
  if (!file || !sig) {
    res.status(400).end();
    return;
  }

  const abs = path.resolve(file);
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
