import { Request, Response, NextFunction } from 'express';

export function cspHeaders(req: Request, res: Response, next: NextFunction) {
  const policy = [
    "default-src 'self'",
    "base-uri 'self'",
    'block-all-mixed-content',
    "font-src 'self' https: data:",
    "frame-ancestors 'self'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self'",
    "script-src-attr 'none'",
    "style-src 'self' https: 'unsafe-inline'",
    'upgrade-insecure-requests',
  ].join('; ');
  res.setHeader('Content-Security-Policy', policy);
  next();
}
