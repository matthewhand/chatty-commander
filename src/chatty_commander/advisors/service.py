"""
Advisor service for handling AI advisor interactions.
"""

from dataclasses import dataclass
from typing import Any

from .context import ContextManager, PlatformType
from .memory import MemoryStore
from .prompting import Persona, build_provider_prompt
from .providers import build_provider_safe


@dataclass
class AdvisorMessage:
    """Incoming message for advisor processing."""
    platform: str
    channel: str
    user: str
    text: str
    username: str | None = None
    metadata: dict[str, Any] | None = None


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

    def __init__(self, config: dict[str, Any]):
        # Accept either a plain dict or a Config-like object with `.advisors`
        base_cfg = getattr(config, "advisors", None)
        if base_cfg is None and isinstance(config, dict):
            base_cfg = config
        elif base_cfg is None:
            # Fallback to empty dict if unsupported type provided
            base_cfg = {}
        self.config = base_cfg

        # Initialize memory store using mapped config keys
        mem_cfg = base_cfg.get('memory', {}) or {}
        self.memory = MemoryStore(
            max_items_per_context=mem_cfg.get('max_items_per_context', 100),
            persist=mem_cfg.get('persistence_enabled', mem_cfg.get('persist', False)),
            persist_path=mem_cfg.get('persistence_path') or mem_cfg.get('persist_path')
        )
        self.provider = build_provider_safe(base_cfg.get('providers', {}))
        self.context_manager = ContextManager(base_cfg.get('context', {}))

        # Check if advisors are enabled
        self.enabled = base_cfg.get('enabled', False)

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

        # Build prompt using context-aware persona and recent memory
        # Fetch memory items for (platform, channel, user)
        memory_items = self.memory.get(platform.value, message.channel, message.user)
        history_text = "\n".join([f"{mi.role}: {mi.content}" for mi in memory_items]) if memory_items else ""
        combined_user_text = f"{history_text}\n{message.text}" if history_text else message.text

        persona = Persona(name=context.persona_id, system=context.system_prompt)
        prompt = build_provider_prompt(self.provider.api_mode, persona, combined_user_text)

        # Generate real LLM response
        try:
            response = self.provider.generate(prompt)
        except Exception as e:
            # Fallback to echo if LLM fails
            response = f"[{self.provider.model}][{self.provider.api_mode}][{context.persona_id}] {message.text} (LLM error: {str(e)})"

        # Add to memory using tri-key (platform, channel, user)
        self.memory.add(platform.value, message.channel, message.user, "user", message.text)
        self.memory.add(platform.value, message.channel, message.user, "assistant", response)

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

    def get_context_stats(self) -> dict[str, Any]:
        """Get statistics about current contexts."""
        return self.context_manager.get_stats()

    def clear_context(self, context_key: str) -> bool:
        """Clear a specific context."""
        return self.context_manager.clear_context(context_key)


