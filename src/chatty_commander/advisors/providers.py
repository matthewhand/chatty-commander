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

"""
Core AI Agent providers for Chatty Commander.

This module defines provider implementations that back the Advisors feature with a
single, consistent abstraction over the LLM backend. It now integrates with the
openai-agents framework to unlock advanced, agent-oriented capabilities (e.g.,
MCP/tooling, persona handoffs) while preserving the existing provider selection
interfaces used throughout the codebase and tests.

Key points:
- CompletionProvider and ResponsesProvider remain as compatibility shims so the
  selection logic and tests can continue to reference familiar providers.
- Each provider now constructs a lightweight `openai_agents.Agent` instance and
  delegates responses via `Agent.chat()`. This keeps the surface area minimal
  while enabling future agent features without invasive changes.
- FallbackProvider composes providers to offer resilience across models/modes.
- When the openai-agents package or an API key is not available, we return stub
  providers that echo a deterministic string suitable for tests and demos.

Configuration keys (subset relevant here):
- model: str — model name or alias (default: "gpt-3.5-turbo")
- llm_api_mode / api_mode: str — "completion" or "responses" (compat shim)
- provider.base_url: Optional[str] — OpenAI-compatible endpoint
- provider.api_key: Optional[str] — API key; also read from env OPENAI_API_KEY

This module is intentionally focused on provider orchestration. Orchestration of
end-to-end advisor interactions (prompt building, memory, context) is handled by
chatty_commander.advisors.service.
"""

import inspect
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any

try:
    # Prefer explicit import of Agent symbol for test patchability.
    from agents import Agent  # type: ignore

    AGENTS_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    Agent = None  # type: ignore
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def _filter_kwargs_for_callable(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return kwargs
    if any(
        param.kind == param.VAR_KEYWORD
        for param in signature.parameters.values()
    ):
        return kwargs
    return {key: value for key, value in kwargs.items() if key in signature.parameters}


def _build_stub_provider(config: dict[str, Any]) -> "LLMProvider":
    api_mode = config.get("llm_api_mode", config.get("api_mode", "completion"))
    if api_mode == "responses":
        stub = StubResponsesProvider(config)
        stub.api_mode = "responses"
        return stub
    stub = StubCompletionProvider(config)
    stub.api_mode = "completion"
    return stub


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.model = config.get("model", "gpt-3.5-turbo")
        # Support both legacy key and new key consistently
        self.api_mode = config.get("llm_api_mode", config.get("api_mode", "completion"))
        # Nested provider config is common; flatten for convenience
        provider_cfg = config.get("provider", {}) or {}
        self.base_url = config.get("base_url", provider_cfg.get("base_url"))
        self.api_key = config.get(
            "api_key", provider_cfg.get("api_key", os.getenv("OPENAI_API_KEY"))
        )
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)

        # Model parameters
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.top_p = config.get("top_p", 1.0)
        self.frequency_penalty = config.get("frequency_penalty", 0.0)
        self.presence_penalty = config.get("presence_penalty", 0.0)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Generate a streaming response from the LLM."""
        pass

    def health_check(self) -> bool:
        """Check if the provider is healthy and accessible."""
        try:
            # Simple test generation
            test_response = self.generate("Test")
            return bool(test_response and len(test_response) > 0)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class CompletionProvider(LLMProvider):
    """Provider for completion API mode using openai-agents with tools, MCP, and handoffs."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if not AGENTS_AVAILABLE:
            raise ImportError(
                "openai-agents SDK not available. Install with: pip install openai-agents"
            )

        # Get tools configuration
        tools_config = config.get("tools", {})
        tools = []

        # Add browser analyst tool if enabled
        if tools_config.get("browser_analyst", {}).get("enabled", True):
            try:
                from ..tools.browser_analyst import browser_analyst_tool_instance

                if browser_analyst_tool_instance:
                    tools.append(browser_analyst_tool_instance)
            except ImportError:
                pass

        # MCP and handoffs configuration (placeholder for future implementation)
        mcp_servers = []
        handoffs = []

        # Initialize Agent client with enhanced capabilities
        agent_kwargs = {
            "name": f"advisor-{self.api_mode}",
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "tools": tools,
            "mcp_servers": mcp_servers,
            "handoffs": handoffs,
            "instructions": config.get(
                "instructions", "You are a helpful AI assistant."
            ),
        }
        filtered_kwargs = _filter_kwargs_for_callable(Agent.__init__, agent_kwargs)
        self.agent = Agent(**filtered_kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion response via Agent.chat()."""
        for attempt in range(self.max_retries):
            try:
                # Agent.chat returns a string (implementation dependent). Keep kwargs for future expansion.
                response = self.agent.chat(prompt)
                return str(response).strip() if response is not None else ""
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

        return "Error: Failed to generate response"

    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Generate streaming response.

        If streaming isn't supported by the agent, fall back to a single chat call.
        """
        try:
            # Minimal behavior: return full text. Streaming can be added when Agent supports it in-tree.
            response = self.agent.chat(prompt)
            return str(response).strip() if response is not None else ""
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            return "Error: Failed to generate streaming response"


class ResponsesProvider(LLMProvider):
    """Provider for responses API mode using openai-agents with tools, MCP, and handoffs."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if not AGENTS_AVAILABLE:
            raise ImportError(
                "openai-agents SDK not available. Install with: pip install openai-agents"
            )

        # Get tools configuration
        tools_config = config.get("tools", {})
        tools = []

        # Add browser analyst tool if enabled
        if tools_config.get("browser_analyst", {}).get("enabled", True):
            try:
                from ..tools.browser_analyst import browser_analyst_tool_instance

                if browser_analyst_tool_instance:
                    tools.append(browser_analyst_tool_instance)
            except ImportError:
                pass

        # MCP and handoffs configuration (placeholder for future implementation)
        mcp_servers = []
        handoffs = []

        # Initialize Agent client with enhanced capabilities
        agent_kwargs = {
            "name": f"advisor-{self.api_mode}",
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "tools": tools,
            "mcp_servers": mcp_servers,
            "handoffs": handoffs,
            "instructions": config.get(
                "instructions",
                "You are a helpful AI assistant with access to various tools.",
            ),
        }
        filtered_kwargs = _filter_kwargs_for_callable(Agent.__init__, agent_kwargs)
        self.agent = Agent(**filtered_kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Agent.chat()."""
        for attempt in range(self.max_retries):
            try:
                response = self.agent.chat(prompt)
                return str(response).strip() if response is not None else ""
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

        return "Error: Failed to generate response"

    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Generate streaming response using Agent.chat() as a fallback."""
        try:
            response = self.agent.chat(prompt)
            return str(response).strip() if response is not None else ""
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            return "Error: Failed to generate streaming response"


class FallbackProvider(LLMProvider):
    """Fallback provider that tries multiple providers in sequence."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.providers: list[LLMProvider] = []

        # Add primary provider
        primary_config = config.copy()
        primary_config["api_mode"] = config.get("primary_api_mode", "completion")
        primary_config["llm_api_mode"] = primary_config.get("api_mode", "completion")
        self.providers.append(self._create_provider(primary_config))

        # Add fallback providers
        fallback_configs = config.get("fallbacks", [])
        for fallback_config in fallback_configs:
            self.providers.append(self._create_provider(fallback_config))

    def _create_provider(self, config: dict[str, Any]) -> LLMProvider:
        """Create provider based on API mode."""
        api_mode = config.get("llm_api_mode", config.get("api_mode", "completion"))

        if api_mode == "completion":
            return CompletionProvider(config)
        elif api_mode == "responses":
            return ResponsesProvider(config)
        else:
            raise ValueError(f"Unknown API mode: {api_mode}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Try providers in sequence until one succeeds."""
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Trying provider {i + 1}/{len(self.providers)}")
                return provider.generate(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {i + 1} failed: {e}")
                if i == len(self.providers) - 1:
                    # Last provider failed
                    return f"Error: All providers failed. Last error: {e}"

        return "Error: No providers available"

    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Try providers in sequence for streaming."""
        for i, provider in enumerate(self.providers):
            try:
                logger.info(
                    f"Trying provider {i + 1}/{len(self.providers)} for streaming"
                )
                return provider.generate_stream(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {i + 1} failed for streaming: {e}")
                if i == len(self.providers) - 1:
                    return f"Error: All providers failed for streaming. Last error: {e}"

        return "Error: No providers available for streaming"

    def health_check(self) -> bool:
        """Check if any provider is healthy."""
        for provider in self.providers:
            if provider.health_check():
                return True
        return False


def build_provider(config: dict[str, Any]) -> LLMProvider:
    """
    Build the appropriate LLM provider based on configuration.

    Args:
        config: Provider configuration dictionary

    Returns:
        Configured LLM provider instance
    """
    api_mode = config.get("llm_api_mode", config.get("api_mode", "completion"))

    # Check if fallback configuration is provided
    if config.get("fallbacks"):
        return FallbackProvider(config)

    # Single provider based on API mode
    if api_mode == "completion":
        return CompletionProvider(config)
    elif api_mode == "responses":
        return ResponsesProvider(config)
    else:
        raise ValueError(f"Unknown API mode: {api_mode}")


# Stub providers for testing when SDK is not available or API key missing
class StubCompletionProvider(LLMProvider):
    """Stub provider for testing."""

    def generate(self, prompt: str, **kwargs) -> str:
        return f"advisor:{self.model}/{self.api_mode} {prompt}"

    def generate_stream(self, prompt: str, **kwargs) -> str:
        return f"advisor:{self.model}/{self.api_mode} {prompt}"


class StubResponsesProvider(LLMProvider):
    """Stub provider for testing."""

    def generate(self, prompt: str, **kwargs) -> str:
        return f"advisor:{self.model}/{self.api_mode} {prompt}"

    def generate_stream(self, prompt: str, **kwargs) -> str:
        return f"advisor:{self.model}/{self.api_mode} {prompt}"


def build_provider_safe(config: dict[str, Any]) -> LLMProvider:
    """
    Build provider with fallback to stubs if openai-agents SDK is not available or no API key is provided.

    Args:
        config: Provider configuration dictionary

    Returns:
        Configured LLM provider instance (real or stub)
    """
    if not AGENTS_AVAILABLE:
        logger.warning("openai-agents SDK not available, using stub providers")
        return _build_stub_provider(config)

    # Check if API key is available
    if "api_key" in config:
        api_key = config.get("api_key")
    elif "provider" in config and "api_key" in config.get("provider", {}):
        api_key = config.get("provider", {}).get("api_key")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No API key provided, using stub providers")
        return _build_stub_provider(config)

    try:
        return build_provider(config)
    except Exception as exc:
        logger.warning("Provider initialization failed, using stub: %s", exc)
        return _build_stub_provider(config)
