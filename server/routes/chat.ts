import { Router } from 'express';

const router = Router();

// Minimal chat handler that can emit tool-call events. When the request body
// contains `{ tool: { name: 'sidecar.open', input: {...} } }` an SSE event is
// streamed to the client so the UI can react to the tool call.
router.post('/', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');

  const tool = req.body?.tool;
  if (tool?.name === 'sidecar.open') {
    const payload = JSON.stringify(tool.input || {});
    res.write('event: sidecar.open\n');
    res.write(`data: ${payload}\n\n`);
  }

  res.write('event: done\n');
  res.write('data: {}\n\n');
  res.end();
});

export default router;
