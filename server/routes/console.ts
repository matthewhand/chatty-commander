import { Router, Response } from "express";

const router = Router();

const clients: Response[] = [];

function broadcastLine(level: string, line: string) {
  const payload = `event: line\ndata: ${JSON.stringify({ level, line })}\n\n`;
  for (const client of clients) {
    client.write(payload);
  }
}

router.get("/stream", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  clients.push(res);

  res.write("event: line\n");
  res.write(`data: ${JSON.stringify({ level: 'info', line: 'ready' })}\n\n`);

  req.on("close", () => {
    const idx = clients.indexOf(res);
    if (idx !== -1) {
      clients.splice(idx, 1);
    }
  });
});

const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;

console.log = (...args: any[]) => {
  broadcastLine("info", args.join(" "));
  originalLog.apply(console, args);
};

console.error = (...args: any[]) => {
  broadcastLine("error", args.join(" "));
  originalError.apply(console, args);
};

console.warn = (...args: any[]) => {
  broadcastLine("warn", args.join(" "));
  originalWarn.apply(console, args);
};

export { broadcastLine };
export default router;
