import { Router } from 'express';
import { build } from '../services/builder.js';

const router = Router();

router.post('/build', async (req, res) => {
  const { entry = '' } = req.body || {};
  try {
    const result = await build(entry);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
