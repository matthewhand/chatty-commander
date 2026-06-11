# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.

"""Coverage-focused tests for ``chatty_commander.llm.manager.LLMManager``.

All real backends (OpenAI / Ollama / local transformers) are replaced with
fakes so the tests are fully hermetic: no network calls, no model downloads,
no API keys required.
"""

from __future__ import annotations

from typing import Any

import pytest

import chatty_commander.llm.manager as manager_mod
from chatty_commander.llm.manager import (
    LLMManager,
    get_default_llm_manager,
    get_global_llm_manager,
)


class FakeBackend:
    """A controllable stand-in for any LLMBackend."""

    def __init__(
        self,
        name: str,
        *,
        available: bool = True,
        response: str = "ok",
        raise_on_generate: Exception | None = None,
    ) -> None:
        self.name = name
        self._available = available
        self._response = response
        self._raise_on_generate = raise_on_generate
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def is_available(self) -> bool:
        return self._available

    def generate_response(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append((prompt, kwargs))
        if self._raise_on_generate is not None:
            raise self._raise_on_generate
        return self._response

    def get_backend_info(self) -> dict[str, Any]:
        return {"backend": self.name, "available": self._available}


@pytest.fixture
def patch_backends(monkeypatch):
    """Patch the backend constructors used inside ``_initialize_backends``.

    Returns a dict you mutate to control which backends are created and how
    they behave. By default every constructor yields an *available* fake.
    """

    registry: dict[str, FakeBackend] = {}

    def make_factory(key: str):
        def factory(*args: Any, **kwargs: Any) -> FakeBackend:
            backend = registry.get(key)
            if backend is None:
                backend = FakeBackend(key)
                registry[key] = backend
            if isinstance(backend, Exception):  # pragma: no cover - defensive
                raise backend
            return backend

        return factory

    # Mock backend is constructed with MockLLMBackend(); give it its own fake.
    def mock_factory(*args: Any, **kwargs: Any) -> FakeBackend:
        backend = registry.get("mock")
        if backend is None:
            backend = FakeBackend("mock")
            registry["mock"] = backend
        return backend

    monkeypatch.setattr(manager_mod, "MockLLMBackend", mock_factory)
    monkeypatch.setattr(manager_mod, "OpenAIBackend", make_factory("openai"))
    monkeypatch.setattr(manager_mod, "OllamaBackend", make_factory("ollama"))
    monkeypatch.setattr(manager_mod, "LocalTransformersBackend", make_factory("local"))

    return registry


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Ensure ambient env vars don't influence backend selection."""
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# --------------------------------------------------------------------------- #
# Construction / backend selection
# --------------------------------------------------------------------------- #


def test_use_mock_only_initializes_mock(patch_backends):
    mgr = LLMManager(use_mock=True)
    assert set(mgr.backends.keys()) == {"mock"}
    assert mgr.get_active_backend_name() == "mock"
    assert mgr.is_available() is True


def test_priority_order_selects_openai_first(patch_backends):
    # All available -> openai wins by priority order.
    mgr = LLMManager()
    assert mgr.get_active_backend_name() == "openai"


def test_falls_through_to_ollama_when_openai_unavailable(patch_backends):
    patch_backends["openai"] = FakeBackend("openai", available=False)
    mgr = LLMManager()
    assert mgr.get_active_backend_name() == "ollama"


def test_falls_through_to_mock_when_all_real_unavailable(patch_backends):
    patch_backends["openai"] = FakeBackend("openai", available=False)
    patch_backends["ollama"] = FakeBackend("ollama", available=False)
    patch_backends["local"] = FakeBackend("local", available=False)
    mgr = LLMManager()
    assert mgr.get_active_backend_name() == "mock"


def test_preferred_backend_used_when_available(patch_backends):
    mgr = LLMManager(preferred_backend="ollama")
    assert mgr.get_active_backend_name() == "ollama"


def test_preferred_backend_falls_back_when_unavailable(patch_backends):
    patch_backends["ollama"] = FakeBackend("ollama", available=False)
    mgr = LLMManager(preferred_backend="ollama")
    # ollama not available -> falls to priority order -> openai
    assert mgr.get_active_backend_name() == "openai"


def test_preferred_backend_unknown_name_ignored(patch_backends):
    mgr = LLMManager(preferred_backend="does-not-exist")
    # Unknown name not in backends -> normal priority order
    assert mgr.get_active_backend_name() == "openai"


def test_preferred_backend_from_env(monkeypatch, patch_backends):
    monkeypatch.setenv("LLM_BACKEND", "local")
    mgr = LLMManager()
    assert mgr.preferred_backend == "local"
    assert mgr.get_active_backend_name() == "local"


def test_backend_init_exception_is_swallowed(monkeypatch, patch_backends):
    def boom(*args: Any, **kwargs: Any):
        raise RuntimeError("cannot init openai")

    monkeypatch.setattr(manager_mod, "OpenAIBackend", boom)
    mgr = LLMManager()
    # openai never registered; next priority backend selected
    assert "openai" not in mgr.backends
    assert mgr.get_active_backend_name() == "ollama"


def test_ollama_and_local_init_exceptions_swallowed(monkeypatch, patch_backends):
    def boom(*args: Any, **kwargs: Any):
        raise RuntimeError("init failure")

    monkeypatch.setattr(manager_mod, "OllamaBackend", boom)
    monkeypatch.setattr(manager_mod, "LocalTransformersBackend", boom)
    mgr = LLMManager()
    # Both failed to register; openai is still available and selected.
    assert "ollama" not in mgr.backends
    assert "local" not in mgr.backends
    assert mgr.get_active_backend_name() == "openai"


# --------------------------------------------------------------------------- #
# generate_response + fallback
# --------------------------------------------------------------------------- #


def test_generate_response_uses_active_backend(patch_backends):
    patch_backends["openai"] = FakeBackend("openai", response="hello-openai")
    mgr = LLMManager()
    out = mgr.generate_response("hi", max_tokens=5)
    assert out == "hello-openai"
    assert mgr.backends["openai"].calls == [("hi", {"max_tokens": 5})]


def test_generate_response_no_backend_raises():
    mgr = LLMManager(use_mock=True)
    mgr.active_backend = None
    with pytest.raises(RuntimeError, match="No LLM backend available"):
        mgr.generate_response("hi")


def test_generate_response_falls_back_on_error(patch_backends):
    patch_backends["openai"] = FakeBackend(
        "openai", raise_on_generate=RuntimeError("rate limited")
    )
    patch_backends["ollama"] = FakeBackend("ollama", response="from-ollama")
    mgr = LLMManager()
    assert mgr.get_active_backend_name() == "openai"
    out = mgr.generate_response("hi")
    assert out == "from-ollama"
    assert mgr.get_active_backend_name() == "ollama"


def test_generate_response_fallback_also_fails_reraises(patch_backends):
    patch_backends["openai"] = FakeBackend(
        "openai", raise_on_generate=RuntimeError("primary fail")
    )
    patch_backends["ollama"] = FakeBackend(
        "ollama", raise_on_generate=ValueError("fallback fail")
    )
    patch_backends["local"] = FakeBackend("local", available=False)
    # mock is available but comes after; fallback picks ollama which fails.
    mgr = LLMManager()
    with pytest.raises(ValueError, match="fallback fail"):
        mgr.generate_response("hi")


def test_generate_response_no_fallback_available_reraises(patch_backends):
    # Only mock backend; it raises and there's nothing after it.
    err = RuntimeError("mock fail")
    patch_backends["mock"] = FakeBackend("mock", raise_on_generate=err)
    mgr = LLMManager(use_mock=True)
    with pytest.raises(RuntimeError, match="mock fail"):
        mgr.generate_response("hi")


# --------------------------------------------------------------------------- #
# _try_fallback
# --------------------------------------------------------------------------- #


def test_try_fallback_returns_false_when_none_available(patch_backends):
    patch_backends["ollama"] = FakeBackend("ollama", available=False)
    patch_backends["local"] = FakeBackend("local", available=False)
    patch_backends["mock"] = FakeBackend("mock", available=False)
    mgr = LLMManager()
    # active is openai; everything after is unavailable.
    assert mgr.get_active_backend_name() == "openai"
    assert mgr._try_fallback() is False


def test_try_fallback_from_unknown_current_scans_all(patch_backends):
    mgr = LLMManager(use_mock=True)
    # Force an active backend whose name isn't in fallback_order list path.
    mgr.active_backend = FakeBackend("ghost")
    assert mgr.get_active_backend_name() == "unknown"
    # candidates = full order; mock is available.
    assert mgr._try_fallback() is True
    assert mgr.get_active_backend_name() == "mock"


# --------------------------------------------------------------------------- #
# get_active_backend_name / info helpers
# --------------------------------------------------------------------------- #


def test_get_active_backend_name_none():
    mgr = LLMManager(use_mock=True)
    mgr.active_backend = None
    assert mgr.get_active_backend_name() == "none"


def test_get_active_backend_name_unknown(patch_backends):
    mgr = LLMManager()
    mgr.active_backend = FakeBackend("stranger")
    assert mgr.get_active_backend_name() == "unknown"


def test_get_backend_info_named_existing(patch_backends):
    mgr = LLMManager()
    info = mgr.get_backend_info("ollama")
    assert info["backend"] == "ollama"


def test_get_backend_info_named_missing(patch_backends):
    mgr = LLMManager()
    info = mgr.get_backend_info("nope")
    assert info == {"error": "Backend nope not found"}


def test_get_backend_info_active(patch_backends):
    mgr = LLMManager()
    info = mgr.get_backend_info()
    assert info["backend"] == "openai"


def test_get_backend_info_no_active(patch_backends):
    mgr = LLMManager()
    mgr.active_backend = None
    assert mgr.get_backend_info() == {"error": "No active backend"}


def test_get_all_backends_info_includes_active_and_errors(patch_backends):
    # Make one backend raise during get_backend_info.
    bad = FakeBackend("local")

    def boom() -> dict[str, Any]:
        raise RuntimeError("info boom")

    bad.get_backend_info = boom  # type: ignore[method-assign]
    patch_backends["local"] = bad

    mgr = LLMManager()
    info = mgr.get_all_backends_info()
    assert info["active"] == "openai"
    assert info["local"] == {"error": "info boom"}
    assert info["openai"]["backend"] == "openai"


# --------------------------------------------------------------------------- #
# switch_backend
# --------------------------------------------------------------------------- #


def test_switch_backend_success(patch_backends):
    mgr = LLMManager()
    assert mgr.switch_backend("ollama") is True
    assert mgr.get_active_backend_name() == "ollama"


def test_switch_backend_unknown(patch_backends):
    mgr = LLMManager()
    assert mgr.switch_backend("nope") is False


def test_switch_backend_unavailable(patch_backends):
    patch_backends["ollama"] = FakeBackend("ollama", available=False)
    mgr = LLMManager()
    assert mgr.switch_backend("ollama") is False
    # active unchanged
    assert mgr.get_active_backend_name() == "openai"


# --------------------------------------------------------------------------- #
# refresh_backends
# --------------------------------------------------------------------------- #


def test_refresh_backends_resets_available_cache_attr(patch_backends):
    mgr = LLMManager()
    # Give a backend the cache attribute that refresh resets.
    target = mgr.backends["openai"]
    target._available = True  # type: ignore[attr-defined]
    mgr.refresh_backends()
    assert target._available is None  # type: ignore[attr-defined]
    # Reselection still yields a valid backend.
    assert mgr.is_available() is True


# --------------------------------------------------------------------------- #
# test_backend
# --------------------------------------------------------------------------- #


def test_test_backend_unknown(patch_backends):
    mgr = LLMManager()
    assert mgr.test_backend("nope") == {"error": "Backend nope not found"}


def test_test_backend_unavailable(patch_backends):
    patch_backends["ollama"] = FakeBackend("ollama", available=False)
    mgr = LLMManager()
    result = mgr.test_backend("ollama")
    assert result == {"error": "Backend ollama not available"}


def test_test_backend_success(patch_backends):
    patch_backends["openai"] = FakeBackend("openai", response="pong")
    mgr = LLMManager()
    result = mgr.test_backend("openai", test_prompt="ping")
    assert result["success"] is True
    assert result["response"] == "pong"
    assert "response_time" in result
    assert result["backend_info"]["backend"] == "openai"
    # max_tokens=20 passed through
    assert mgr.backends["openai"].calls[-1] == ("ping", {"max_tokens": 20})


def test_test_backend_generation_error(patch_backends):
    patch_backends["openai"] = FakeBackend(
        "openai", raise_on_generate=RuntimeError("gen boom")
    )
    mgr = LLMManager()
    result = mgr.test_backend("openai")
    assert result["error"] == "gen boom"
    assert result["backend_info"]["backend"] == "openai"


# --------------------------------------------------------------------------- #
# Module-level convenience functions
# --------------------------------------------------------------------------- #


def test_get_default_llm_manager(patch_backends):
    mgr = get_default_llm_manager(use_mock=True)
    assert isinstance(mgr, LLMManager)
    assert mgr.get_active_backend_name() == "mock"


def test_get_global_llm_manager_is_cached(patch_backends):
    # Reset module global to avoid cross-test contamination.
    manager_mod._default_manager = None
    first = get_global_llm_manager(use_mock=True)
    second = get_global_llm_manager(use_mock=True)
    assert first is second
    manager_mod._default_manager = None
