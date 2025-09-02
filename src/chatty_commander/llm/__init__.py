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
    "CommandProcessor",
]
