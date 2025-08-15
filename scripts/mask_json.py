#!/usr/bin/env python3
import json, re, sys, pathlib
SUSPECT = re.compile(r"(pass(word)?|secret|token|key|api|auth|bearer|credential|cookie|session|private)", re.I)
def scrub(x):
    if isinstance(x, dict): return {k: ("***REDACTED***" if SUSPECT.search(k or "") else scrub(v)) for k,v in x.items()}
    if isinstance(x, list): return [scrub(v) for v in x]
    if isinstance(x, str) and SUSPECT.search(x): return "***REDACTED***"
    return x
p = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
if not p or not p.exists(): print(f"# mask_json.py: file not found: {p}", file=sys.stderr); sys.exit(1)
json.dump(scrub(json.load(open(p, "r", encoding="utf-8"))), sys.stdout, indent=2, ensure_ascii=False); print()
