"""
LLM provider implementations for advisors.

Supports both completion and responses API modes with real OpenAI SDK integration.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.api_mode = config.get('api_mode', 'completion')
        self.base_url = config.get('base_url', None)
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30)
        
        # Model parameters
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.top_p = config.get('top_p', 1.0)
        self.frequency_penalty = config.get('frequency_penalty', 0.0)
        self.presence_penalty = config.get('presence_penalty', 0.0)
    
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
    """Provider for completion API mode (broad compatibility)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with: pip install openai")
        
        # Initialize OpenAI client
        client_kwargs = {
            'timeout': self.timeout,
        }
        
        if self.api_key:
            client_kwargs['api_key'] = self.api_key
        
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion response."""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=kwargs.get('temperature', self.temperature),
                    max_tokens=kwargs.get('max_tokens', self.max_tokens),
                    top_p=kwargs.get('top_p', self.top_p),
                    frequency_penalty=kwargs.get('frequency_penalty', self.frequency_penalty),
                    presence_penalty=kwargs.get('presence_penalty', self.presence_penalty),
                    stream=False
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return "Error: Failed to generate response"
    
    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Generate streaming response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True
            )
            
            # Collect streamed response
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            
            return full_response.strip()
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            return "Error: Failed to generate streaming response"


class ResponsesProvider(LLMProvider):
    """Provider for responses API mode (upstream default, limited third-party support)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with: pip install openai")
        
        # Initialize OpenAI client
        client_kwargs = {
            'timeout': self.timeout,
        }
        
        if self.api_key:
            client_kwargs['api_key'] = self.api_key
        
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using responses API."""
        for attempt in range(self.max_retries):
            try:
                response = self.client.beta.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=kwargs.get('temperature', self.temperature),
                    max_tokens=kwargs.get('max_tokens', self.max_tokens),
                    top_p=kwargs.get('top_p', self.top_p),
                    frequency_penalty=kwargs.get('frequency_penalty', self.frequency_penalty),
                    presence_penalty=kwargs.get('presence_penalty', self.presence_penalty),
                    stream=False
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return "Error: Failed to generate response"
    
    def generate_stream(self, prompt: str, **kwargs) -> str:
        """Generate streaming response using responses API."""
        try:
            response = self.client.beta.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True
            )
            
            # Collect streamed response
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            
            return full_response.strip()
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            return "Error: Failed to generate streaming response"


class FallbackProvider(LLMProvider):
    """Fallback provider that tries multiple providers in sequence."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.providers: List[LLMProvider] = []
        
        # Add primary provider
        primary_config = config.copy()
        primary_config['api_mode'] = config.get('primary_api_mode', 'completion')
        self.providers.append(self._create_provider(primary_config))
        
        # Add fallback providers
        fallback_configs = config.get('fallbacks', [])
        for fallback_config in fallback_configs:
            self.providers.append(self._create_provider(fallback_config))
    
    def _create_provider(self, config: Dict[str, Any]) -> LLMProvider:
        """Create provider based on API mode."""
        api_mode = config.get('api_mode', 'completion')
        
        if api_mode == 'completion':
            return CompletionProvider(config)
        elif api_mode == 'responses':
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
                logger.info(f"Trying provider {i + 1}/{len(self.providers)} for streaming")
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


def build_provider(config: Dict[str, Any]) -> LLMProvider:
    """
    Build the appropriate LLM provider based on configuration.
    
    Args:
        config: Provider configuration dictionary
        
    Returns:
        Configured LLM provider instance
    """
    api_mode = config.get('llm_api_mode', 'completion')
    
    # Check if fallback configuration is provided
    if config.get('fallbacks'):
        return FallbackProvider(config)
    
    # Single provider based on API mode
    if api_mode == 'completion':
        return CompletionProvider(config)
    elif api_mode == 'responses':
        return ResponsesProvider(config)
    else:
        raise ValueError(f"Unknown API mode: {api_mode}")


# Stub providers for testing when OpenAI SDK is not available
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


def build_provider_safe(config: Dict[str, Any]) -> LLMProvider:
    """
    Build provider with fallback to stubs if OpenAI SDK is not available or no API key is provided.
    
    Args:
        config: Provider configuration dictionary
        
    Returns:
        Configured LLM provider instance (real or stub)
    """
    if not OPENAI_AVAILABLE:
        logger.warning("OpenAI SDK not available, using stub providers")
        api_mode = config.get('llm_api_mode', 'completion')
        
        if api_mode == 'completion':
            stub = StubCompletionProvider(config)
            stub.api_mode = 'completion'
            return stub
        elif api_mode == 'responses':
            stub = StubResponsesProvider(config)
            stub.api_mode = 'responses'
            return stub
        else:
            stub = StubCompletionProvider(config)
            stub.api_mode = 'completion'
            return stub
    
    # Check if API key is available
    api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))
    if not api_key:
        logger.warning("No OpenAI API key provided, using stub providers")
        api_mode = config.get('llm_api_mode', 'completion')
        
        if api_mode == 'completion':
            stub = StubCompletionProvider(config)
            stub.api_mode = 'completion'
            return stub
        elif api_mode == 'responses':
            stub = StubResponsesProvider(config)
            stub.api_mode = 'responses'
            return stub
        else:
            stub = StubCompletionProvider(config)
            stub.api_mode = 'completion'
            return stub
    
    return build_provider(config)


