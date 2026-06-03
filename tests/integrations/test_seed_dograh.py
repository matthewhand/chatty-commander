"""Tests for scripts/seed_dograh.py — the CI dograh bootstrap script.

Covers the two non-trivial branches: signup-409-falls-back-to-login and
workflow-name-already-present-is-reused. Pure unit tests using respx;
no live dograh required.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import httpx
import pytest
import respx

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_dograh.py"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_dograh", SEED_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["seed_dograh"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def seed():
    return _load_seed_module()


BASE = "http://dograh.test"


@respx.mock
def test_ensure_user_signup_path(seed) -> None:
    respx.post(f"{BASE}/api/v1/auth/signup").mock(
        return_value=httpx.Response(200, json={"token": "jwt-new"})
    )
    with httpx.Client(base_url=BASE) as client:
        tok = seed._ensure_user(client, "u@example.com", "pw", "U")
    assert tok == "jwt-new"


@respx.mock
def test_ensure_user_falls_back_to_login_on_409(seed) -> None:
    respx.post(f"{BASE}/api/v1/auth/signup").mock(
        return_value=httpx.Response(409, json={"detail": "Email already registered"})
    )
    login_route = respx.post(f"{BASE}/api/v1/auth/login").mock(
        return_value=httpx.Response(200, json={"token": "jwt-existing"})
    )
    with httpx.Client(base_url=BASE) as client:
        tok = seed._ensure_user(client, "u@example.com", "pw", "U")
    assert tok == "jwt-existing"
    assert login_route.called


@respx.mock
def test_ensure_user_raises_on_unexpected_status(seed) -> None:
    respx.post(f"{BASE}/api/v1/auth/signup").mock(
        return_value=httpx.Response(500, json={"detail": "boom"})
    )
    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(httpx.HTTPStatusError):
            seed._ensure_user(client, "u@example.com", "pw", "U")


@respx.mock
def test_ensure_workflow_reuses_existing_by_name(seed) -> None:
    respx.get(f"{BASE}/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "other"},
                {"id": 7, "name": "cc-ci-seed-workflow"},
            ],
        )
    )
    create_route = respx.post(f"{BASE}/api/v1/workflow/create/definition").mock(
        return_value=httpx.Response(200, json={"id": 999})
    )
    with httpx.Client(base_url=BASE) as client:
        wid = seed._ensure_workflow(client, "cc-ci-seed-workflow")
    assert wid == 7
    assert not create_route.called  # didn't duplicate


@respx.mock
def test_ensure_workflow_creates_when_missing(seed) -> None:
    respx.get(f"{BASE}/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(200, json=[])
    )
    create_route = respx.post(f"{BASE}/api/v1/workflow/create/definition").mock(
        return_value=httpx.Response(200, json={"id": 12})
    )
    with httpx.Client(base_url=BASE) as client:
        wid = seed._ensure_workflow(client, "fresh")
    assert wid == 12
    assert create_route.called


@respx.mock
def test_mint_api_key_returns_raw_key(seed) -> None:
    respx.post(f"{BASE}/api/v1/user/api-keys").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "api_key": "dgr_seed_test", "key_prefix": "dgr_seed"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        key = seed._mint_api_key(client, "ci")
    assert key == "dgr_seed_test"


@respx.mock
def test_ensure_workflow_picks_lowest_id_on_duplicate_names(seed) -> None:
    """If two workflows share the seed name, return the lowest id deterministically."""
    respx.get(f"{BASE}/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 9, "name": "seed"},
                {"id": 3, "name": "seed"},
                {"id": 7, "name": "other"},
            ],
        )
    )
    with httpx.Client(base_url=BASE) as client:
        wid = seed._ensure_workflow(client, "seed")
    assert wid == 3


@respx.mock
def test_main_with_output_redacts_stdout(
    seed, tmp_path, capsys, monkeypatch
) -> None:
    """The whole point of --output: the API key must NOT appear in stdout
    when a file destination is given, because CI step logs are captured."""
    respx.post(f"{BASE}/api/v1/auth/signup").mock(
        return_value=httpx.Response(200, json={"token": "jwt-xyz"})
    )
    respx.post(f"{BASE}/api/v1/user/api-keys").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "api_key": "dgr_SUPER_SECRET_KEY_VALUE",
                "key_prefix": "dgr_SUPE",
            },
        )
    )
    respx.get(f"{BASE}/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post(f"{BASE}/api/v1/workflow/create/definition").mock(
        return_value=httpx.Response(200, json={"id": 42})
    )

    out_file = tmp_path / "seed.env"
    rc = seed.main(["--base-url", BASE, "--output", str(out_file)])
    assert rc == 0

    captured = capsys.readouterr()
    # Stdout must NOT contain the raw secret.
    assert "dgr_SUPER_SECRET_KEY_VALUE" not in captured.out
    # Should show redacted prefix instead.
    assert "redacted" in captured.out
    # File must contain the real key for the test runner to consume.
    assert "DOGRAH_API_KEY=dgr_SUPER_SECRET_KEY_VALUE" in out_file.read_text()
    # File must be owner-only readable (best-effort; POSIX only).
    import stat

    mode = out_file.stat().st_mode & 0o777
    assert mode == 0o600


@respx.mock
def test_main_without_output_still_prints_env_block(
    seed, capsys
) -> None:
    """Legacy interactive mode: no --output means stdout carries the env."""
    respx.post(f"{BASE}/api/v1/auth/signup").mock(
        return_value=httpx.Response(200, json={"token": "jwt"})
    )
    respx.post(f"{BASE}/api/v1/user/api-keys").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "api_key": "dgr_interactive", "key_prefix": "dgr_inte"}
        )
    )
    respx.get(f"{BASE}/api/v1/workflow/fetch").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.post(f"{BASE}/api/v1/workflow/create/definition").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )

    rc = seed.main(["--base-url", BASE])
    assert rc == 0
    captured = capsys.readouterr()
    assert "DOGRAH_API_KEY=dgr_interactive" in captured.out
