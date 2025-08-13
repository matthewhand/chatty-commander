import { Router } from 'express';

const router = Router();

router.post('/build', (req, res) => {
  res.json({ bundleUrl: '', version: '0.0.0', sha256: '' });
});

export default router;
