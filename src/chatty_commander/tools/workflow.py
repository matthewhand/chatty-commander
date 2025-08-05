from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .builder import build_openapi_schema, generate_markdown_docs
from .fs_ops import ensure_dir, write_json, write_text

logger = logging.getLogger(__name__)


def generate_docs(output_dir: Path | None = None) -> dict[str, Path]:
    """
    Orchestrate API documentation generation.

    - Builds OpenAPI schema (pure)
    - Generates Markdown docs (pure)
    - Writes artifacts to disk under docs/ (or provided output_dir)
    - Returns mapping of artifact names to their output paths
    """
    project_root = Path.cwd()
    docs_dir = Path(output_dir) if output_dir else (project_root / "docs")
    ensure_dir(docs_dir)

    # Build artifacts (pure)
    openapi_spec: dict[str, Any] = build_openapi_schema()
    markdown_docs: str = generate_markdown_docs()

    # Write artifacts (side-effects isolated here)
    openapi_file = docs_dir / "openapi.json"
    write_json(openapi_file, openapi_spec)
    logger.info("✅ OpenAPI specification saved to %s", openapi_file)

    markdown_file = docs_dir / "API.md"
    write_text(markdown_file, markdown_docs)
    logger.info("✅ Markdown documentation saved to %s", markdown_file)

    index_content = """
# ChattyCommander Documentation

## Available Documentation

- [API Documentation](API.md) - Comprehensive API reference
- [OpenAPI Specification](openapi.json) - Machine-readable API spec

## Quick Start

1. Start the server: `python main.py --web --no-auth`
2. Open the API docs: [http://localhost:8100/docs](http://localhost:8100/docs)
3. Test the API: `curl http://localhost:8100/api/v1/status`

## Interactive Documentation

When the server is running, you can access interactive API documentation at:
- Swagger UI: [http://localhost:8100/docs](http://localhost:8100/docs)
- ReDoc: [http://localhost:8100/redoc](http://localhost:8100/redoc)
""".lstrip()

    index_file = docs_dir / "README.md"
    write_text(index_file, index_content)
    logger.info("✅ Documentation index saved to %s", index_file)

    logger.info("🎉 Documentation generation complete!")
    logger.info("📁 Documentation available in: %s", docs_dir)

    return {
        "openapi": openapi_file,
        "markdown": markdown_file,
        "index": index_file,
    }
