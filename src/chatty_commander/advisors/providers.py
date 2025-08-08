from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class LLMProvider:
    def generate(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class CompletionProvider(LLMProvider):
    model: str
    base_url: str | None = None

    def generate(self, prompt: str) -> str:
        # Stubbed completion path for tests
        return f"prov:completion model={self.model} prompt={prompt}"


@dataclass
class ResponsesProvider(LLMProvider):
    model: str
    base_url: str | None = None

    def generate(self, prompt: str) -> str:
        # Stubbed responses path for tests
        return f"prov:responses model={self.model} prompt={prompt}"


def build_provider(config: Any) -> LLMProvider:
    advisors = getattr(config, "advisors", {})
    mode = advisors.get("llm_api_mode", "completion").lower()
    model = advisors.get("model", "gpt-oss20b")
    base_url = advisors.get("provider", {}).get("base_url")
    if mode == "responses":
        return ResponsesProvider(model=model, base_url=base_url)
    return CompletionProvider(model=model, base_url=base_url)


