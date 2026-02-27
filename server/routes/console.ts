import { Router } from "express";

const router = Router();

router.get("/stream", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.write("event: line\n");
  res.write('data: {"level":"info","line":"ready"}\n\n');
});

export default router;
