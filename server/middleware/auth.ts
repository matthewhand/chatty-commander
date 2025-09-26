import { Request, Response, NextFunction } from "express";

export function auth(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token || token !== "valid_token_for_advisors") {
    // Simple token check; in production use JWT or similar
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
}
