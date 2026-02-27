import { Router } from "express";
import { chat } from "../services/llm";

const router = Router();

router.post("/", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");

  const send = (event: string, data: any) => {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  // Check for sidecar.open tool call in request
  const tool = req.body?.tool;
  if (tool?.name === 'sidecar.open') {
    const payload = JSON.stringify(tool.input || {});
    res.write('event: sidecar.open\n');
    res.write(`data: ${payload}\n\n`);
  }

  // simulate streaming of an assistant response with a tool call
  send("chunk", { id: "assistant", delta: "Hello from ChattyCommander. " });
  send("tool_call", { id: "tool-1", name: "clock" });
  send("tool_result", {
    id: "tool-1",
    delta: "The current time is high noon.",
  });
  send("chunk", { id: "assistant", delta: "Hope that helps!" });
  send("done", {});

  res.end();
});

export default router;
