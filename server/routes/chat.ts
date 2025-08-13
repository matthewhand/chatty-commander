import { Router } from 'express';

const router = Router();

router.post('/', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.write('event: done\n');
  res.write('data: {}\n\n');
  res.end();
});

export default router;
