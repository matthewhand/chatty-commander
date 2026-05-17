#!/usr/bin/env python3
"""Bootstrap a Dograh OSS stack with a known user, API key, and workflow.

Designed for CI but safe to run locally. Idempotent at the user and
workflow layer:

  * If the seed user already exists, we log in instead of signing up.
  * If a workflow with the seed name already exists in the org, we
    reuse it instead of creating a duplicate.

The API key layer is intentionally NOT idempotent: dograh only returns
the raw key value at creation time and there is no way to recover an
existing key, so each seed run mints a fresh one. Old keys accumulate
in the database; archive them manually via the UI / API if needed.

Output: writes credentials in ``.env`` format to the path given by
``--output`` (and always echoes to stdout) so a downstream CI step can::

    python scripts/seed_dograh.py --output scripts/dograh_seed.env
    set -a && source scripts/dograh_seed.env && set +a
    DOGRAH_LIVE=1 pytest tests/integrations/

Exit code is non-zero on any HTTP error, so CI fails loudly if dograh
isn't reachable or auth breaks.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import cast

import httpx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DOGRAH_BASE_URL", "http://localhost:8020"),
    )
    parser.add_argument("--email", default="cc-ci@example.com")
    parser.add_argument(
        "--password",
        default=os.environ.get("DOGRAH_SEED_PASSWORD", "ci-only-not-secret-Vm8K9Lz"),
        help="Seed user password. Override via DOGRAH_SEED_PASSWORD env in real CI.",
    )
    parser.add_argument("--name", default="CI CC")
    parser.add_argument("--workflow-name", default="cc-ci-seed-workflow")
    parser.add_argument("--api-key-name", default="cc-ci-key")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write env-format credentials. "
        "Always also echoed to stdout.",
    )
    args = parser.parse_args(argv)

    base = args.base_url.rstrip("/")
    with httpx.Client(base_url=base, timeout=30.0) as client:
        token = _ensure_user(client, args.email, args.password, args.name)
        client.headers["Authorization"] = f"Bearer {token}"
        api_key = _mint_api_key(client, args.api_key_name)

        # Switch to API-key auth for the workflow step so we exercise the
        # key end-to-end before handing it back to the caller.
        client.headers.pop("Authorization", None)
        client.headers["X-API-Key"] = api_key
        workflow_id = _ensure_workflow(client, args.workflow_name)

    env_block = (
        f"DOGRAH_BASE_URL={base}\n"
        f"DOGRAH_API_KEY={api_key}\n"
        f"DOGRAH_SEED_WORKFLOW_ID={workflow_id}\n"
    )

    if args.output:
        args.output.write_text(env_block)
        print(f"# wrote credentials to {args.output}", file=sys.stderr)

    sys.stdout.write(env_block)
    return 0


def _ensure_user(
    client: httpx.Client, email: str, password: str, name: str
) -> str:
    """Return a JWT for the seed user, signing them up if missing."""
    r = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "name": name},
    )
    if r.status_code == 409:
        # Already registered — fall through to login.
        r = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
    r.raise_for_status()
    return cast(str, r.json()["token"])


def _mint_api_key(client: httpx.Client, key_name: str) -> str:
    """Mint a fresh API key. Old keys with the same name remain in dograh."""
    r = client.post("/api/v1/user/api-keys", json={"name": key_name})
    r.raise_for_status()
    return cast(str, r.json()["api_key"])


def _ensure_workflow(client: httpx.Client, workflow_name: str) -> int:
    """Return the id of the seed workflow, creating it if missing."""
    r = client.get("/api/v1/workflow/fetch")
    r.raise_for_status()
    payload = r.json()
    items = payload if isinstance(payload, list) else payload.get("items", [])
    for wf in items:
        if wf.get("name") == workflow_name:
            return int(wf["id"])
    r = client.post(
        "/api/v1/workflow/create/definition",
        json={"name": workflow_name, "workflow_definition": {}},
    )
    r.raise_for_status()
    return int(r.json()["id"])


if __name__ == "__main__":
    sys.exit(main())
