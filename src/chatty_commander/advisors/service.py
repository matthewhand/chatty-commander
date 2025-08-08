"""
Advisor service for handling AI advisor interactions.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .memory import MemoryStore
from .providers import build_provider
from .prompting import resolve_persona, build_provider_prompt
from .context import ContextManager, PlatformType


@dataclass
class AdvisorMessage:
    """Incoming message for advisor processing."""
    platform: str
    channel: str
    user: str
    text: str
    username: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AdvisorReply:
    """Response from advisor processing."""
    reply: str
    context_key: str
    persona_id: str
    model: str
    api_mode: str


class AdvisorsService:
    """Core service for handling advisor messages and responses."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory = MemoryStore(config.get('memory', {}))
        self.provider = build_provider(config.get('providers', {}))
        self.context_manager = ContextManager(config.get('context', {}))
        
        # Check if advisors are enabled
        self.enabled = config.get('enabled', False)
    
    def handle_message(self, message: AdvisorMessage) -> AdvisorReply:
        """
        Process an incoming message and return advisor response.
        
        Args:
            message: The incoming message to process
            
        Returns:
            AdvisorReply with response and metadata
        """
        if not self.enabled:
            raise RuntimeError("Advisors are not enabled")
        
        # Handle special commands
        if message.text.startswith("summarize "):
            return self._handle_summarize_command(message)
        
        # Get or create context for this identity
        platform = PlatformType(message.platform.lower())
        context = self.context_manager.get_or_create_context(
            platform=platform,
            channel=message.channel,
            user_id=message.user,
            username=message.username,
            **(message.metadata or {})
        )
        
        # Build prompt using context-aware persona
        prompt = build_provider_prompt(
            provider=self.provider,
            system_prompt=context.system_prompt,
            user_message=message.text,
            memory_items=self.memory.get(context.memory_key)
        )
        
        # Generate response (for now, echo with context info)
        response = f"[{self.provider.model}][{self.provider.api_mode}][{context.persona_id}] {message.text}"
        
        # Add to memory
        self.memory.add(context.memory_key, "user", message.text)
        self.memory.add(context.memory_key, "assistant", response)
        
        return AdvisorReply(
            reply=response,
            context_key=context.identity.context_key,
            persona_id=context.persona_id,
            model=self.provider.model,
            api_mode=self.provider.api_mode
        )
    
    def _handle_summarize_command(self, message: AdvisorMessage) -> AdvisorReply:
        """Handle the summarize command."""
        from .tools.browser_analyst import browser_analyst_tool
        
        url = message.text[10:]  # Remove "summarize "
        summary = browser_analyst_tool(url)
        
        return AdvisorReply(
            reply=f"Summary of {url}: {summary}",
            context_key="summarize",
            persona_id="analyst",
            model=self.provider.model,
            api_mode=self.provider.api_mode
        )
    
    def switch_persona(self, context_key: str, persona_id: str) -> bool:
        """Switch persona for a specific context."""
        return self.context_manager.switch_persona(context_key, persona_id)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about current contexts."""
        return self.context_manager.get_stats()
    
    def clear_context(self, context_key: str) -> bool:
        """Clear a specific context."""
        return self.context_manager.clear_context(context_key)


