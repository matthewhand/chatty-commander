"""
LLM integration module for ChattyCommander.

Provides flexible LLM backends with automatic fallback:
1. OpenAI API (if OPENAI_API_KEY set)
2. Ollama (local server, default ollama:11434)
3. Local transformers (gpt-oss:20b via transformers)

Environment variables:
- OPENAI_API_KEY: Enable OpenAI API backend
- OPENAI_API_BASE: Override OpenAI base URL
- OLLAMA_HOST: Override Ollama host (default: ollama:11434)
- LLM_BACKEND: Force specific backend (openai, ollama, local)
"""

from .backends import LLMBackend, LocalTransformersBackend, OllamaBackend, OpenAIBackend
from .manager import LLMManager
from .processor import CommandProcessor

__all__ = [
    "LLMBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "LocalTransformersBackend",
    "LLMManager",
    "CommandProcessor"
]
