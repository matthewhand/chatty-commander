import { Router } from 'express';

const router = Router();

router.get('/file', (req, res) => {
  res.status(404).end();
});

export default router;
