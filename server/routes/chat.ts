import { Router } from 'express';
import { chat } from '../services/llm';

const router = Router();

router.post('/', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  try {
    for await (const ev of chat(req.body?.messages ?? [])) {
      if (ev.type === 'chunk') {
        res.write('event: chunk\n');
        res.write(`data: ${JSON.stringify({ id: ev.id, delta: ev.delta })}\n\n`);
      } else if (ev.type === 'tool_call') {
        res.write('event: tool_call\n');
        res.write(`data: ${JSON.stringify({ id: ev.id, name: ev.name, args: ev.args })}\n\n`);
      } else if (ev.type === 'tool_result') {
        res.write('event: tool_result\n');
        res.write(`data: ${JSON.stringify({ id: ev.id, result: ev.result })}\n\n`);
      }
    }
    res.write('event: done\n');
    res.write('data: {}\n\n');
  } catch (err: any) {
    res.write('event: error\n');
    res.write(`data: ${JSON.stringify({ message: err?.message || String(err) })}\n\n`);
  } finally {
    res.end();
  }
});

export default router;
