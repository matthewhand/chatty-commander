from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv  # noqa: ARG001
    try:
        from .cli.cli import main as cli_main  # type: ignore
    except Exception:
        return 0
    rc = cli_main()
    return int(rc or 0)

if __name__ == "__main__":
    raise SystemExit(main())
