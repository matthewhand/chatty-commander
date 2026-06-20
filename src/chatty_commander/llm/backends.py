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
LLM backend implementations with automatic fallback strategy.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available and ready."""
        pass

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt."""
        pass

    @abstractmethod
    def get_backend_info(self) -> dict[str, Any]:
        """Get backend information."""
        pass


class OpenAIBackend(LLMBackend):
    """OpenAI API backend."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, **kwargs):
        self.api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
        )
        self.base_url = (
            base_url
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.max_retries = kwargs.get("max_retries", 3)
        self.timeout = kwargs.get("timeout", 30.0)
        self._client: Any = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            logger.debug("No OpenAI API key provided")
            return

        try:
            import openai

            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0  # We handle retries manually
            )
            logger.info(f"Initialized OpenAI client with base URL: {self.base_url}")
        except ImportError:
            logger.warning(
                "OpenAI library not available. Install with: pip install openai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI backend is configured and ready.

        This is a CHEAP check: it confirms a client was initialized and an API
        key is present. It must NOT make a (billed) network request such as a
        ``chat.completions.create`` probe — backend *selection* calls this and
        should never trigger paid API usage. Any real failure is surfaced
        lazily on the actual ``generate_response`` call.
        """
        return bool(self._client) and bool(self.api_key)

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API with retries."""
        if not self._client:
            raise RuntimeError("OpenAI client not available")

        import time

        model = kwargs.get("model", getattr(self, "model", "gpt-3.5-turbo"))
        max_tokens = kwargs.get("max_tokens", 150)
        temperature = kwargs.get("temperature", 0.7)

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()  # type: ignore[no-any-return]
            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI generation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    sleep_time = 1.0 * (2 ** attempt)  # Exponential backoff
                    time.sleep(sleep_time)

        raise RuntimeError(f"OpenAI generation failed after {self.max_retries} retries: {last_error}")

    def get_backend_info(self) -> dict[str, Any]:
        """Get OpenAI backend information."""
        return {
            "backend": "openai",
            "available": self.is_available(),
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "max_retries": self.max_retries,
        }


class OllamaBackend(LLMBackend):
    """Ollama local server backend."""

    def __init__(self, host: str | None = None, model: str = "gpt-oss:20b"):
        self.host = host or os.getenv("OLLAMA_HOST", "ollama:11434")
        self.model = model
        self.base_url = f"http://{self.host}"
        self._available: bool | None = None
        logger.info(f"Initialized Ollama backend: {self.base_url}, model: {self.model}")

    def _validate_url(self, url: str) -> None:
        """Reject an outbound Ollama URL that fails the SSRF policy.

        Applied immediately before every outbound request so a switched or
        otherwise unvalidated ``OLLAMA_HOST`` can never be hit, regardless of
        whether ``is_available`` (which is cacheable/skippable) ran first.
        """
        from chatty_commander.utils.url_validator import is_safe_url

        if not is_safe_url(url):
            logger.warning(f"Ollama URL {url} rejected by security policy.")
            raise RuntimeError("Ollama URL rejected by security policy")

    def is_available(self) -> bool:
        """Check if the Ollama server is reachable.

        This is a CHEAP check: it does a single short-timeout ``GET
        /api/tags`` to confirm the server responds. It must NEVER trigger a
        model *pull* (which can block for minutes) — backend *selection* calls
        this, and selection must not download models. Auto-pull, if needed,
        happens lazily inside :meth:`generate_response`.
        """
        if self._available is not None:
            return self._available

        tags_url = f"{self.base_url}/api/tags"
        try:
            import httpx

            self._validate_url(tags_url)

            # Quick reachability probe with a short timeout; never pulls.
            with httpx.Client() as client:
                response = client.get(tags_url, timeout=5, follow_redirects=False)
            self._available = response.status_code == 200
            if self._available:
                logger.debug(f"Ollama server reachable at {self.base_url}")
            else:
                logger.debug(f"Ollama server not responding: {response.status_code}")

        except ImportError:
            logger.warning("httpx library not available for Ollama backend")
            self._available = False
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            self._available = False

        return self._available

    def _try_pull_model(self):
        """Try to pull the model if not available."""
        try:
            import httpx

            pull_url = f"{self.base_url}/api/pull"
            self._validate_url(pull_url)

            logger.info(f"Attempting to pull model {self.model}...")
            with httpx.Client() as client:
                response = client.post(
                    pull_url,
                    json={"name": self.model},
                    timeout=300,  # 5 minutes timeout for model download
                    follow_redirects=False,
                )

                if response.status_code == 200:
                    logger.info(f"Successfully pulled model {self.model}")
                else:
                    logger.warning(
                        f"Failed to pull model {self.model}: {response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"Error pulling model {self.model}: {e}")

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama backend not available")

        try:
            import httpx

            max_tokens = kwargs.get("max_tokens", 150)
            temperature = kwargs.get("temperature", 0.7)

            generate_url = f"{self.base_url}/api/generate"
            self._validate_url(generate_url)

            with httpx.Client() as client:
                response = client.post(
                    generate_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                        },
                    },
                    timeout=30,
                    follow_redirects=False,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()  # type: ignore[no-any-return]
                else:
                    raise RuntimeError(f"Ollama request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def get_backend_info(self) -> dict[str, Any]:
        """Get Ollama backend information."""
        return {
            "backend": "ollama",
            "available": self.is_available(),
            "host": self.host,
            "base_url": self.base_url,
            "model": self.model,
        }


class LocalTransformersBackend(LLMBackend):
    """Local HuggingFace transformers backend.

    Defaults to ``microsoft/DialoGPT-medium`` — a small conversational model
    that downloads quickly and runs on CPU. Pass ``model_name`` to use a larger
    model. (The previous docstring claimed gpt-oss:20b, which was never the
    default and would not fit most local machines.)
    """

    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        # Use a smaller model that actually exists for now
        self.model_name = model_name
        self._model: Any = None
        self._tokenizer: Any = None
        self._device: str | None = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize local transformers model."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading local model: {self.model_name}")

            # Determine device
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self._device}")

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
                device_map="auto" if self._device == "cuda" else None,
            )

            if self._device == "cpu":
                self._model = self._model.to(self._device)

            # Add pad token if missing
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            logger.info(f"Successfully loaded local model: {self.model_name}")

        except ImportError as e:
            logger.warning(f"Transformers dependencies not available: {e}")
            logger.info("Install with: pip install torch transformers")
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")

    def is_available(self) -> bool:
        """Check if local transformers backend is available."""
        return self._model is not None and self._tokenizer is not None

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using local transformers model."""
        if not self.is_available():
            raise RuntimeError("Local transformers backend not available")

        try:
            import torch

            max_tokens = kwargs.get("max_tokens", 150)
            temperature = kwargs.get("temperature", 0.7)

            # Tokenize input
            inputs = self._tokenizer.encode(prompt, return_tensors="pt").to(
                self._device
            )

            # Generate response
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs),
                )

            # Decode response (skip the input tokens)
            response_tokens = outputs[0][inputs.shape[1] :]
            response = self._tokenizer.decode(response_tokens, skip_special_tokens=True)

            return response.strip()  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Local transformers generation failed: {e}")
            raise

    def get_backend_info(self) -> dict[str, Any]:
        """Get local transformers backend information."""
        return {
            "backend": "local_transformers",
            "available": self.is_available(),
            "model_name": self.model_name,
            "device": self._device,
        }


class MockLLMBackend(LLMBackend):
    """Mock LLM backend for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or [
            "I understand you want to execute a command. Let me help with that.",
            "Based on your request, I'll trigger the appropriate action.",
            "Processing your voice command now.",
            "Command received and understood.",
            "I'll execute that action for you.",
        ]
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using mock."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        logger.debug(f"Mock LLM response: '{response}'")
        return response

    def get_backend_info(self) -> dict[str, Any]:
        """Retrieve backend info."""
        return {
            "backend": "mock",
            "available": True,
            "responses_count": len(self.responses),
            "call_count": self.call_count,
        }
