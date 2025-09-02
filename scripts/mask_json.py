#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import pathlib
import re
import sys

SUSPECT = re.compile(
    r"(pass(word)?|secret|token|key|api|auth|bearer|credential|cookie|session|private)",
    re.I,
)


def scrub(x):
    if isinstance(x, dict):
        return {
            k: ("***REDACTED***" if SUSPECT.search(k or "") else scrub(v))
            for k, v in x.items()
        }
    if isinstance(x, list):
        return [scrub(v) for v in x]
    if isinstance(x, str) and SUSPECT.search(x):
        return "***REDACTED***"
    return x


p = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not p or not p.exists():
    print(f"# mask_json.py: file not found: {p}", file=sys.stderr)
    sys.exit(1)
json.dump(
    scrub(json.load(open(p, encoding="utf-8"))),
    sys.stdout,
    indent=2,
    ensure_ascii=False,
)
print()
