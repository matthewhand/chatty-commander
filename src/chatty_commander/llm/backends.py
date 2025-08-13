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

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self._client = None
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
                base_url=self.base_url
            )
            logger.info(f"Initialized OpenAI client with base URL: {self.base_url}")
        except ImportError:
            logger.warning("OpenAI library not available. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI backend is available."""
        if not self._client:
            return False

        try:
            # Test with a minimal request
            response = self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.debug(f"OpenAI availability check failed: {e}")
            return False

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        if not self._client:
            raise RuntimeError("OpenAI client not available")

        try:
            model = kwargs.get("model", "gpt-3.5-turbo")
            max_tokens = kwargs.get("max_tokens", 150)
            temperature = kwargs.get("temperature", 0.7)

            response = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def get_backend_info(self) -> dict[str, Any]:
        """Get OpenAI backend information."""
        return {
            "backend": "openai",
            "available": self.is_available(),
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        }


class OllamaBackend(LLMBackend):
    """Ollama local server backend."""

    def __init__(self, host: str | None = None, model: str = "gpt-oss:20b"):
        self.host = host or os.getenv("OLLAMA_HOST", "ollama:11434")
        self.model = model
        self.base_url = f"http://{self.host}"
        self._available = None
        logger.info(f"Initialized Ollama backend: {self.base_url}, model: {self.model}")

    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        if self._available is not None:
            return self._available

        try:
            import requests

            # Check if Ollama server is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                # Check if our model is available
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]

                if self.model in model_names:
                    self._available = True
                    logger.info(f"Ollama model {self.model} is available")
                else:
                    logger.info(f"Ollama server running but model {self.model} not found. Available: {model_names}")
                    # Try to pull the model
                    self._try_pull_model()
                    self._available = self.model in [m.get("name", "") for m in requests.get(f"{self.base_url}/api/tags").json().get("models", [])]
            else:
                self._available = False
                logger.debug(f"Ollama server not responding: {response.status_code}")

        except ImportError:
            logger.warning("Requests library not available for Ollama backend")
            self._available = False
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            self._available = False

        return self._available

    def _try_pull_model(self):
        """Try to pull the model if not available."""
        try:
            import requests

            logger.info(f"Attempting to pull model {self.model}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300  # 5 minutes timeout for model download
            )

            if response.status_code == 200:
                logger.info(f"Successfully pulled model {self.model}")
            else:
                logger.warning(f"Failed to pull model {self.model}: {response.status_code}")

        except Exception as e:
            logger.warning(f"Error pulling model {self.model}: {e}")

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama backend not available")

        try:
            import requests

            max_tokens = kwargs.get("max_tokens", 150)
            temperature = kwargs.get("temperature", 0.7)

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
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
    """Local transformers backend using gpt-oss:20b."""

    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        # Use a smaller model that actually exists for now
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        self._device = None
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
                device_map="auto" if self._device == "cuda" else None
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
            inputs = self._tokenizer.encode(prompt, return_tensors="pt").to(self._device)

            # Generate response
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs)
                )

            # Decode response (skip the input tokens)
            response_tokens = outputs[0][inputs.shape[1]:]
            response = self._tokenizer.decode(response_tokens, skip_special_tokens=True)

            return response.strip()

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
            "I'll execute that action for you."
        ]
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def generate_response(self, prompt: str, **kwargs) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        logger.debug(f"Mock LLM response: '{response}'")
        return response

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "backend": "mock",
            "available": True,
            "responses_count": len(self.responses),
            "call_count": self.call_count,
        }
