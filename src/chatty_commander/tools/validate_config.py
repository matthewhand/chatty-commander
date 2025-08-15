from __future__ import annotations

import json
import pathlib
import sys

CFG = pathlib.Path("config.json")


def main() -> int:
    if not CFG.exists():
        print("config.json not found", file=sys.stderr)
        return 2
    data = json.loads(CFG.read_text())
    commands = set((data.get("commands") or {}).keys())
    missing: list[str] = []
    for state, names in (data.get("state_models") or {}).items():
        for name in names or []:
            if name not in commands:
                missing.append(f"{state}:{name}")
    if missing:
        print("Config validation: MISSING commands referenced in state_models:")
        for m in sorted(missing):
            print(" -", m)
        return 1
    print("Config validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
