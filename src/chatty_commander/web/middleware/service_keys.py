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

"""Named, scoped service-to-service API keys (AUTHZ_DESIGN.md §5, Phase 3).

This is the **opt-in** registry layer that lets the coarse global ``X-API-Key``
gate accept more than one key. Config shape (extends the same ``auth`` dict the
middleware already reads)::

    "auth": {
      "api_key": "legacy-single-key",          # STILL honored → scope ["*"]
      "service_keys": {
        "discord-bridge":  {"key_hash": "$2b$…", "scopes": ["command:write"], "active": true},
        "metrics-scraper": {"key_hash": "$2b$…", "scopes": ["status:read"],   "active": true}
      }
    }

Back-compat contract
---------------------
* When **no** ``auth.service_keys`` block is configured, :func:`resolve_service_key_scopes`
  returns ``None`` for every input — the registry is effectively absent and the
  middleware falls back to the legacy single-key path byte-for-byte.
* The legacy plaintext ``auth.api_key`` is handled entirely by the middleware
  and is treated as a **wildcard** key (scopes ``["*"]``); this module never
  sees it.

Lookup
------
Service keys are stored **bcrypt-hashed**. A presented plaintext key is checked
with :func:`bcrypt.checkpw` against each *active* candidate's ``key_hash``. We
iterate the full active candidate set (no short-circuit on first failure) so the
work — and timing — does not depend on *which* key matched, mirroring the
constant-time intent already used for the legacy key compare. The first active
key whose hash verifies wins and its configured scopes are returned.
"""

from __future__ import annotations

import logging
from typing import Any

import bcrypt

logger = logging.getLogger(__name__)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def service_keys_config(config_manager: Any) -> dict[str, Any]:
    """Return the ``auth.service_keys`` mapping from either Config shape.

    Mirrors the middleware's dual lookup: ``config_manager.auth`` (DummyConfig /
    test objects) or ``config_manager.config["auth"]`` (the real ``Config``).
    Returns an empty dict when no service keys are configured.
    """
    if config_manager is None:
        return {}
    auth_attr = getattr(config_manager, "auth", None)
    if isinstance(auth_attr, dict):
        auth = auth_attr
    else:
        cfg = getattr(config_manager, "config", None)
        auth = _as_dict(cfg.get("auth")) if isinstance(cfg, dict) else {}
    return _as_dict(auth.get("service_keys"))


def _verify_key_hash(provided: str, key_hash: Any) -> bool:
    """Constant-time bcrypt check; tolerant of malformed/empty hashes.

    Mirrors ``routes/auth.py:_verify_password`` so the codebase has a single
    bcrypt-verify idiom.
    """
    if not isinstance(key_hash, str) or not key_hash:
        return False
    try:
        return bcrypt.checkpw(provided.encode("utf-8"), key_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _scopes_from(raw: Any) -> list[str]:
    return [s for s in raw if isinstance(s, str)] if isinstance(raw, list) else []


def resolve_service_key_scopes(
    config_manager: Any, provided_key: str | None
) -> list[str] | None:
    """Resolve a presented X-API-Key to its service-key scopes.

    Returns the matched **active** service key's scopes (possibly an empty list
    if the key declares none). Returns ``None`` when:

    * no ``auth.service_keys`` block is configured (registry absent), or
    * ``provided_key`` is blank/missing, or
    * no active service key's ``key_hash`` verifies against ``provided_key``.

    Inactive keys (``"active": false`` or missing/non-true) are never
    candidates, so a rotated-out key is rejected even though its hash is still
    on file.
    """
    if not provided_key:
        return None
    registry = service_keys_config(config_manager)
    if not registry:
        return None

    matched_scopes: list[str] | None = None
    # Iterate every active candidate (no early break) so timing does not reveal
    # which named key matched.
    for name, spec in registry.items():
        if not isinstance(spec, dict):
            continue
        if spec.get("active") is not True:
            continue
        if _verify_key_hash(provided_key, spec.get("key_hash")):
            if matched_scopes is None:
                logger.debug("Service key matched: %s", name)
                matched_scopes = _scopes_from(spec.get("scopes"))
    return matched_scopes
