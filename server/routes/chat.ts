import { Router } from 'express';

const router = Router();

router.post('/', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  const send = (event: string, data: any) => {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // simulate streaming of an assistant response with a tool call
  send('chunk', { id: 'assistant', delta: 'Hello from ChattyCommander. ' });
  send('tool_call', { id: 'tool-1', name: 'clock' });
  send('tool_result', { id: 'tool-1', delta: 'The current time is high noon.' });
  send('chunk', { id: 'assistant', delta: 'Hope that helps!' });
  send('done', {});

  res.end();
});

export default router;
