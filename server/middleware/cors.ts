import { Request, Response, NextFunction } from "express";

export function corsHeaders(req: Request, res: Response, next: NextFunction) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  next();
}
