import { Router } from 'express';
import { build } from '../services/builder.js';

const router = Router();

// Build the canvas bundle and return metadata needed by the client.
router.post('/build', async (req, res, next) => {
  try {
    const { entry, asciiOnly } = req.body || {};
    const result = await build(entry, asciiOnly);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

export default router;
