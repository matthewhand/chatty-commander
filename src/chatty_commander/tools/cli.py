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

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .workflow import generate_docs

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    # Accept unknown options to avoid pytest-provided flags (-q, test paths) breaking parsing
    parser = argparse.ArgumentParser(
        prog="generate-api-docs",
        description="Generate ChattyCommander API documentation (OpenAPI JSON and Markdown).",
        add_help=False,
        allow_abbrev=False,
    )
    # Provide our own -h/--help since add_help=False
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs"),
        help="Output directory for docs (defaults to ./docs).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be specified multiple times).",
    )
    # Accept and ignore any extra args (e.g., pytest passes -k, -q, test paths)
    parser.add_argument("extra", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    # Use parse_known_args to swallow unknown options like -q before REMAINDER
    if argv is None:
        # Let argparse look at sys.argv but still not fail on unknown by using parse_known_args
        args, _unknown = parser.parse_known_args()
    else:
        args, _unknown = parser.parse_known_args(argv)
    return args


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)

    try:
        result = generate_docs(output_dir=args.output)
        logger.info("Generated docs: %s", {k: str(v) for k, v in result.items()})
        return 0
    except SystemExit as e:
        # When invoked via runpy/run_module, pytest may inject flags causing argparse/SystemExit.
        # Our parser swallows unknowns; if a SystemExit still bubbles, map non-int to 1.
        return int(e.code) if isinstance(e.code, int) else 1
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to generate docs: %s", e)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
