import json
from pathlib import Path

from chatty_commander.web.web_mode import create_app


def test_runtime_openapi_matches_docs_file_on_key_paths():
    """
    Parity check: ensure key API paths exist in both runtime schema and docs/openapi.json.
    This is a tolerant check to avoid flakiness when non-key paths change.
    """
    app = create_app(no_auth=True)
    runtime = app.openapi()

    docs_path = Path("docs/openapi.json")
    assert docs_path.is_file(), "docs/openapi.json is missing; generate with make api-docs"
    docs_schema = json.loads(docs_path.read_text(encoding="utf-8"))

    assert "paths" in runtime and isinstance(runtime["paths"], dict)
    assert "paths" in docs_schema and isinstance(docs_schema["paths"], dict)

    runtime_paths = set(runtime["paths"].keys())
    docs_paths = set(docs_schema["paths"].keys())

    # Key endpoints we expect to exist in both
    key = {
        "/api/v1/health",
        "/api/v1/status",
        "/api/v1/config",
        "/api/v1/state",
        "/api/v1/command",
        "/api/v1/version",
    }

    missing_in_runtime = key - runtime_paths
    missing_in_docs = key - docs_paths

    assert not missing_in_runtime, f"Runtime schema missing key paths: {sorted(missing_in_runtime)}"
    assert not missing_in_docs, f"docs/openapi.json missing key paths: {sorted(missing_in_docs)}"
