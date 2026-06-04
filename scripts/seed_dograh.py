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
``--output``. When ``--output`` is given, only a redacted summary goes
to stdout — the raw key never appears in build logs that may be publicly
readable::

    python scripts/seed_dograh.py --output scripts/dograh_seed.env
    set -a && source scripts/dograh_seed.env && set +a
    DOGRAH_LIVE=1 pytest tests/integrations/

If ``--output`` is omitted, the env block goes to stdout but the API key
is **masked** (``dgr_****last4``) by default so it never lands in
terminal scrollback. Pass ``--print-secret`` to echo the raw key for
interactive ``source <(...)`` use::

    source <(python scripts/seed_dograh.py --print-secret)

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


def _mask_api_key(api_key: str) -> str:
    """Return a non-secret placeholder for an API key, e.g. ``dgr_****1a2b``.

    Keeps the ``dgr_`` prefix (if present) and the last 4 chars so the key
    is recognisable without leaking its secret body into logs/scrollback.
    """
    last4 = api_key[-4:] if len(api_key) >= 4 else api_key
    if api_key.startswith("dgr_"):
        return f"dgr_****{last4}"
    return f"****{last4}"


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
        "Stdout only gets a redacted summary when this is set.",
    )
    parser.add_argument(
        "--print-secret",
        action="store_true",
        help="In stdout mode (no --output), echo the raw API key instead of a "
        "masked placeholder. Use only for interactive `source <(...)`; the raw "
        "key will land in terminal scrollback.",
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
        # Write file with owner-only perms so other users on the host
        # can't read the freshly-minted API key out of /tmp.
        args.output.write_text(env_block)
        try:
            args.output.chmod(0o600)
        except OSError:
            pass
        # Print a redacted summary to stdout — never the key itself, so
        # CI step logs don't leak it.
        sys.stdout.write(
            f"# wrote credentials to {args.output}\n"
            f"# DOGRAH_BASE_URL={base}\n"
            f"# DOGRAH_API_KEY={_mask_api_key(api_key)} (redacted)\n"
            f"# DOGRAH_SEED_WORKFLOW_ID={workflow_id}\n"
        )
        return 0

    if args.print_secret:
        # Explicit opt-in: emit the raw env block for `source <(...)`.
        sys.stdout.write(env_block)
        return 0

    # No --output and no --print-secret: print a masked env block so the
    # raw key never lands in terminal scrollback, plus a hint about the
    # two ways to obtain the real key.
    sys.stdout.write(
        f"DOGRAH_BASE_URL={base}\n"
        f"DOGRAH_API_KEY={_mask_api_key(api_key)}\n"
        f"DOGRAH_SEED_WORKFLOW_ID={workflow_id}\n"
        "# API key masked. Re-run with --print-secret to echo the raw key, "
        "or --output FILE to write it to a 0600 file.\n"
    )
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
    """Return the id of the seed workflow, creating it if missing.

    If multiple workflows share the seed name (shouldn't happen but
    possible via concurrent seed runs), returns the lowest id for
    determinism and logs the choice.
    """
    r = client.get("/api/v1/workflow/fetch")
    r.raise_for_status()
    payload = r.json()
    items = payload if isinstance(payload, list) else payload.get("items", [])
    matching_ids = sorted(
        int(wf["id"]) for wf in items if wf.get("name") == workflow_name
    )
    if matching_ids:
        chosen = matching_ids[0]
        if len(matching_ids) > 1:
            print(
                f"# WARN: {len(matching_ids)} workflows named "
                f"{workflow_name!r} exist (ids={matching_ids}); reusing {chosen}",
                file=sys.stderr,
            )
        else:
            print(
                f"# reusing existing workflow id={chosen} name={workflow_name!r}",
                file=sys.stderr,
            )
        return chosen
    r = client.post(
        "/api/v1/workflow/create/definition",
        json={"name": workflow_name, "workflow_definition": {}},
    )
    r.raise_for_status()
    new_id = int(r.json()["id"])
    print(
        f"# created workflow id={new_id} name={workflow_name!r}", file=sys.stderr
    )
    return new_id


if __name__ == "__main__":
    sys.exit(main())
