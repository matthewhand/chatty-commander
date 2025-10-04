import { Router } from "express";
import { readFile } from "fs/promises";
import { exec as execCb } from "child_process";
import { promisify } from "util";

const exec = promisify(execCb);
const router = Router();

router.get("/file", async (req, res) => {
  const filePath = req.query.path;
  if (typeof filePath !== "string") {
    res.status(400).json({ error: "path required" });
    return;
  }

  const isDiff = req.query.diff === "1" || req.query.diff === "true";

  try {
    if (isDiff) {
      const { stdout } = await exec(`git diff HEAD -- ${filePath}`);
      res.json({ content: stdout });
    } else {
      const content = await readFile(filePath, "utf8");
      res.json({ content });
    }
  } catch (err) {
    res.status(404).json({ error: "file not found" });
  }
});

export default router;
