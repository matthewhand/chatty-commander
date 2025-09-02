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
Ollama Provider for ChattyCommander Advisors

This provider integrates with Ollama to support local models like gpt-oss:20b.
It follows the same interface as other providers but communicates with the Ollama API.
"""

import json
import logging
import time
from collections.abc import Generator
from typing import Any

import requests

from ..advisors.providers import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Provider for Ollama local model serving."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Ollama-specific configuration
        self.ollama_host = config.get("ollama_host", "http://localhost:11434")
        self.model = config.get("model", "gpt-oss:20b")

        # Override base_url for Ollama compatibility
        self.base_url = f"{self.ollama_host}/api"

        # Ollama-specific parameters
        self.stream = config.get("stream", False)
        self.keep_alive = config.get("keep_alive", "5m")
        self.num_ctx = config.get("num_ctx", 2048)
        self.num_predict = config.get("num_predict", self.max_tokens)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "chatty-commander/1.0"}
        )

    def _make_request(
        self, endpoint: str, payload: dict[str, Any]
    ) -> requests.Response:
        """Make HTTP request to Ollama API with retries."""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url, json=payload, timeout=self.timeout, stream=self.stream
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Ollama request attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError(
            f"Failed to connect to Ollama after {self.max_retries} attempts"
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Ollama model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # Non-streaming for this method
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "num_ctx": kwargs.get("num_ctx", self.num_ctx),
                "num_predict": kwargs.get("num_predict", self.num_predict),
            },
            "keep_alive": self.keep_alive,
        }

        try:
            response = self._make_request("generate", payload)
            result = response.json()

            if "response" in result:
                return result["response"].strip()
            else:
                logger.error(f"Unexpected Ollama response format: {result}")
                return "Error: Invalid response from Ollama"

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"Error: Failed to generate response - {e}"

    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate streaming response from Ollama model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "num_ctx": kwargs.get("num_ctx", self.num_ctx),
                "num_predict": kwargs.get("num_predict", self.num_predict),
            },
            "keep_alive": self.keep_alive,
        }

        try:
            url = f"{self.base_url}/generate"
            response = self.session.post(
                url, json=payload, timeout=self.timeout, stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"Error: Failed to stream response - {e}"

    def generate_stream_text(self, prompt: str, **kwargs) -> str:
        """Generate streaming response and return as concatenated string."""
        try:
            chunks = list(self.generate_stream(prompt, **kwargs))
            return "".join(chunks)
        except Exception as e:
            logger.error(f"Ollama streaming generation failed: {e}")
            return f"Error: Failed to generate streaming response - {e}"

    def health_check(self) -> bool:
        """Check if Ollama is healthy and the model is available."""
        try:
            # Check if Ollama is running
            response = self.session.get(f"{self.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]

            # Check if our model is available
            if self.model not in model_names:
                logger.warning(
                    f"Model {self.model} not found in Ollama. Available: {model_names}"
                )
                return False

            # Test simple generation
            test_response = self.generate("Hello")
            return bool(
                test_response
                and len(test_response) > 0
                and not test_response.startswith("Error:")
            )

        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            response = self.session.get(f"{self.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model.get("name", "") for model in models]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    def pull_model(self, model_name: str | None = None) -> bool:
        """Pull/download a model in Ollama."""
        target_model = model_name or self.model

        try:
            payload = {"name": target_model}
            response = self._make_request("pull", payload)

            # Handle streaming pull response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if data.get("status"):
                            logger.info(f"Pulling {target_model}: {data['status']}")
                        if data.get("error"):
                            logger.error(f"Pull error: {data['error']}")
                            return False
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Successfully pulled model: {target_model}")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model {target_model}: {e}")
            return False


def create_ollama_provider(config: dict[str, Any]) -> OllamaProvider:
    """Factory function to create Ollama provider."""
    return OllamaProvider(config)


# Register with provider factory
def build_ollama_provider(config: dict[str, Any]) -> OllamaProvider:
    """Build Ollama provider for integration with advisor system."""
    return OllamaProvider(config)
