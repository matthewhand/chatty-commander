"""Thin HTTP client for the Dograh OSS REST API.

Dograh runs as a separate docker stack (see `docker-compose.dograh.yml`).
This module never starts dograh or assumes it is reachable; calls fail
with a clear ``DograhUnavailableError`` when configuration is missing or
the service is down.

Auth: dograh API keys (``dgr_*``) are passed via the ``X-API-Key``
header, **not** ``Authorization: Bearer``. Mint a key with:

    POST /api/v1/user/api-keys   (authenticated with a JWT)

then set ``DOGRAH_API_KEY`` and ``DOGRAH_BASE_URL`` in the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class DograhError(RuntimeError):
    """Base error for dograh integration failures."""


class DograhUnavailableError(DograhError):
    """Raised when dograh is not configured or not reachable."""


@dataclass
class DograhConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "DograhConfig":
        base_url = os.environ.get("DOGRAH_BASE_URL", "").rstrip("/")
        api_key = os.environ.get("DOGRAH_API_KEY", "")
        if not base_url or not api_key:
            raise DograhUnavailableError(
                "DOGRAH_BASE_URL and DOGRAH_API_KEY must both be set to use the "
                "dograh integration. See docker-compose.dograh.yml and the "
                "/api/v1/user/api-keys endpoint."
            )
        return cls(base_url=base_url, api_key=api_key)


class DograhClient:
    """Minimal sync client for dograh's REST surface.

    Methods cover the Phase 1 integration scope: health, workflow
    listing, telephony call initiation, and generic workflow run
    creation. Add more methods here as new CC ↔ dograh touchpoints
    come online.
    """

    def __init__(self, config: DograhConfig | None = None) -> None:
        self._config = config or DograhConfig.from_env()
        self._client = httpx.Client(
            base_url=self._config.base_url,
            headers={"X-API-Key": self._config.api_key},
            timeout=self._config.timeout_seconds,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DograhClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        """Return dograh's /api/v1/health payload. Does not require auth."""
        r = self._client.get("/api/v1/health")
        r.raise_for_status()
        return r.json()

    def list_workflows(
        self, status: str | None = None
    ) -> list[dict[str, Any]]:
        """List workflows in the caller's selected organization.

        Wraps GET /api/v1/workflow/fetch. ``status`` may be ``active``,
        ``archived``, or a comma-separated combination.
        """
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = status
        r = self._client.get("/api/v1/workflow/fetch", params=params)
        r.raise_for_status()
        payload = r.json()
        if isinstance(payload, list):
            return payload
        return payload.get("items", [])

    def initiate_call(
        self,
        workflow_id: int,
        phone_number: str | None = None,
        telephony_configuration_id: int | None = None,
    ) -> dict[str, Any]:
        """Place an outbound phone call via the configured telephony provider.

        Wraps POST /api/v1/telephony/initiate-call. Used by the
        ``dograh_call`` command action.

        Returns 400 ``telephony_not_configured`` if no provider
        (Twilio/Vonage/etc.) is set up in dograh — that's expected when
        running the OSS stack without telephony credentials, and the
        caller should surface it as a config error rather than a bug.
        """
        body: dict[str, Any] = {"workflow_id": workflow_id}
        if phone_number is not None:
            body["phone_number"] = phone_number
        if telephony_configuration_id is not None:
            body["telephony_configuration_id"] = telephony_configuration_id
        r = self._client.post("/api/v1/telephony/initiate-call", json=body)
        r.raise_for_status()
        return r.json()

    def create_workflow_run(
        self, workflow_id: int, mode: str = "chat", name: str = "cc-run"
    ) -> dict[str, Any]:
        """Trigger a non-telephony workflow run (chat or test mode).

        Wraps POST /api/v1/workflow/{workflow_id}/runs.
        Use ``initiate_call`` for telephony — that endpoint creates the
        run internally with phone-number context already attached.
        """
        r = self._client.post(
            f"/api/v1/workflow/{workflow_id}/runs",
            json={"mode": mode, "name": name},
        )
        r.raise_for_status()
        return r.json()
