import { Router } from 'express';
import { build } from '../services/builder.js';

const router = Router();

router.post('/build', async (req, res) => {
  const entry = req.body?.entry;
  if (typeof entry !== 'string' || entry.length === 0) {
    res.status(400).json({ error: 'entry is required' });
    return;
  }
  try {
    const result = await build(entry);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err?.message || String(err) });
  }
});

export default router;
