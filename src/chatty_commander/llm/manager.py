"""
LLM Manager with automatic backend selection and fallback.

Tries backends in order:
1. OpenAI API (if OPENAI_API_KEY set)
2. Ollama (if server available)
3. Local transformers (if dependencies available)
4. Mock (always available)
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

from .backends import (
    LLMBackend,
    LocalTransformersBackend,
    MockLLMBackend,
    OllamaBackend,
    OpenAIBackend,
)

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM backends with automatic selection and fallback."""

    def __init__(
        self,
        preferred_backend: str | None = None,
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
        ollama_host: str | None = None,
        ollama_model: str = "gpt-oss:20b",
        local_model: str = "microsoft/DialoGPT-medium",
        use_mock: bool = False
    ):
        self.preferred_backend = preferred_backend or os.getenv("LLM_BACKEND")
        self.use_mock = use_mock

        # Initialize all backends
        self.backends: dict[str, LLMBackend] = {}
        self._initialize_backends(
            openai_api_key, openai_base_url,
            ollama_host, ollama_model,
            local_model
        )

        # Select active backend
        self.active_backend: LLMBackend | None = None
        self._select_backend()

        logger.info(f"LLM Manager initialized with backend: {self.get_active_backend_name()}")

    def _initialize_backends(
        self,
        openai_api_key: str | None,
        openai_base_url: str | None,
        ollama_host: str | None,
        ollama_model: str,
        local_model: str
    ):
        """Initialize all available backends."""

        # Always initialize mock backend
        self.backends["mock"] = MockLLMBackend()

        if self.use_mock:
            logger.info("Using mock LLM backend only")
            return

        # OpenAI backend
        try:
            self.backends["openai"] = OpenAIBackend(
                api_key=openai_api_key,
                base_url=openai_base_url
            )
        except Exception as e:
            logger.debug(f"Failed to initialize OpenAI backend: {e}")

        # Ollama backend
        try:
            self.backends["ollama"] = OllamaBackend(
                host=ollama_host,
                model=ollama_model
            )
        except Exception as e:
            logger.debug(f"Failed to initialize Ollama backend: {e}")

        # Local transformers backend
        try:
            self.backends["local"] = LocalTransformersBackend(model_name=local_model)
        except Exception as e:
            logger.debug(f"Failed to initialize local transformers backend: {e}")

    def _select_backend(self):
        """Select the best available backend."""

        # If preferred backend specified, try it first
        if self.preferred_backend and self.preferred_backend in self.backends:
            backend = self.backends[self.preferred_backend]
            if backend.is_available():
                self.active_backend = backend
                logger.info(f"Using preferred backend: {self.preferred_backend}")
                return
            else:
                logger.warning(f"Preferred backend {self.preferred_backend} not available, falling back")

        # Try backends in priority order
        priority_order = ["openai", "ollama", "local", "mock"]

        for backend_name in priority_order:
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.is_available():
                    self.active_backend = backend
                    logger.info(f"Selected backend: {backend_name}")
                    return

        # Fallback to mock if nothing else works
        self.active_backend = self.backends["mock"]
        logger.warning("All backends failed, using mock backend")

    def is_available(self) -> bool:
        """Check if any backend is available."""
        return self.active_backend is not None

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using active backend."""
        if not self.active_backend:
            raise RuntimeError("No LLM backend available")

        try:
            return self.active_backend.generate_response(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Generation failed with {self.get_active_backend_name()}: {e}")

            # Try to fallback to next available backend
            if self._try_fallback():
                logger.info(f"Falling back to {self.get_active_backend_name()}")
                return self.active_backend.generate_response(prompt, **kwargs)
            else:
                raise

    def _try_fallback(self) -> bool:
        """Try to fallback to next available backend."""
        current_backend = self.get_active_backend_name()

        # Get backends to try (excluding current)
        fallback_order = ["openai", "ollama", "local", "mock"]
        try:
            current_index = fallback_order.index(current_backend)
            candidates = fallback_order[current_index + 1:]
        except ValueError:
            candidates = fallback_order

        for backend_name in candidates:
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.is_available():
                    self.active_backend = backend
                    return True

        return False

    def get_active_backend_name(self) -> str:
        """Get name of active backend."""
        if not self.active_backend:
            return "none"

        for name, backend in self.backends.items():
            if backend is self.active_backend:
                return name

        return "unknown"

    def get_backend_info(self, backend_name: str | None = None) -> dict[str, Any]:
        """Get information about a specific backend or active backend."""
        if backend_name:
            if backend_name in self.backends:
                return self.backends[backend_name].get_backend_info()
            else:
                return {"error": f"Backend {backend_name} not found"}
        else:
            if self.active_backend:
                return self.active_backend.get_backend_info()
            else:
                return {"error": "No active backend"}

    def get_all_backends_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all backends."""
        info = {}
        for name, backend in self.backends.items():
            try:
                info[name] = backend.get_backend_info()
            except Exception as e:
                info[name] = {"error": str(e)}

        info["active"] = self.get_active_backend_name()
        return info

    def switch_backend(self, backend_name: str) -> bool:
        """Switch to a specific backend."""
        if backend_name not in self.backends:
            logger.error(f"Backend {backend_name} not available")
            return False

        backend = self.backends[backend_name]
        if not backend.is_available():
            logger.error(f"Backend {backend_name} not available")
            return False

        self.active_backend = backend
        logger.info(f"Switched to backend: {backend_name}")
        return True

    def refresh_backends(self):
        """Refresh backend availability and reselect if needed."""
        logger.info("Refreshing backend availability...")

        # Reset availability cache for backends that support it
        for backend in self.backends.values():
            if hasattr(backend, '_available'):
                backend._available = None

        # Reselect best backend
        self._select_backend()
        logger.info(f"Active backend after refresh: {self.get_active_backend_name()}")

    def test_backend(self, backend_name: str, test_prompt: str = "Hello") -> dict[str, Any]:
        """Test a specific backend with a simple prompt."""
        if backend_name not in self.backends:
            return {"error": f"Backend {backend_name} not found"}

        backend = self.backends[backend_name]

        try:
            if not backend.is_available():
                return {"error": f"Backend {backend_name} not available"}

            start_time = time.time()
            response = backend.generate_response(test_prompt, max_tokens=20)
            end_time = time.time()

            return {
                "success": True,
                "response": response,
                "response_time": end_time - start_time,
                "backend_info": backend.get_backend_info()
            }

        except Exception as e:
            return {
                "error": str(e),
                "backend_info": backend.get_backend_info()
            }


# Convenience function for quick LLM access
def get_default_llm_manager(**kwargs) -> LLMManager:
    """Get a default LLM manager with standard configuration."""
    return LLMManager(**kwargs)


# Global instance for easy access (optional)
_default_manager: LLMManager | None = None

def get_global_llm_manager(**kwargs) -> LLMManager:
    """Get or create global LLM manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = LLMManager(**kwargs)
    return _default_manager
