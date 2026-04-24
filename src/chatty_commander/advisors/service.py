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

"""Advisor service for handling AI advisor interactions."""

from dataclasses import dataclass
from typing import Any

from ..avatars.thinking_state import get_thinking_manager
from . import providers as providers_module
from .context import ContextManager, PlatformType
from .conversation_engine import create_conversation_engine
from .memory import MemoryStore
from .providers import build_provider_safe as build_provider_safe

_DEFAULT_BUILD_PROVIDER_SAFE = build_provider_safe


def _get_provider_builder():
    if build_provider_safe is not _DEFAULT_BUILD_PROVIDER_SAFE:
        return build_provider_safe
    return providers_module.build_provider_safe


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
        # Validate input exists
        elif base_cfg is None:
            # Fallback to empty dict if unsupported type provided
            base_cfg = {}
        self.config = base_cfg

        # Initialize memory store using mapped config keys
        mem_cfg = base_cfg.get("memory", {}) or {}
        self.memory = MemoryStore(
            max_items_per_context=mem_cfg.get("max_items_per_context", 100),
            persist=mem_cfg.get("persistence_enabled", mem_cfg.get("persist", False)),
            persist_path=mem_cfg.get("persistence_path") or mem_cfg.get("persist_path"),
        )
        provider_builder = _get_provider_builder()
        self.provider = provider
    def _get_persona_config(self, context) -> dict:
        """Extract persona configuration from context or config."""
        personas_dict = self.config.get("personas", {}) or self.config.get(
            "context", {}
        ).get("personas", {})
        persona_config = personas_dict.get(context.persona_id, {})
        
        if isinstance(persona_config, str):
            return {"prompt": persona_config, "name": context.persona_id}
        return persona_config

    def _generate_llm_response(self, user_input: str, persona_config: dict, context) -> str:
        """Generate LLM response with fallback handling."""
        enhanced_prompt = self.conversation_engine.build_enhanced_prompt(
            user_input=user_input,
            user_id=f"{context.platform}:{context.channel}:{context.user}",
            persona_config=persona_config,
            current_mode=getattr(self.config, "current_mode", "chatty"),
        )
        
        if hasattr(self, "llm_manager") and self.llm_manager:
            return self.llm_manager.generate_response(
                enhanced_prompt,
                model=getattr(self.llm_manager.active_backend, "model", "gpt-3.5-turbo"),
                max_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.7)
            )
        else:
            return self.provider.generate(enhanced_prompt)

    def _handle_mode_switch(self, response: str) -> str:
        """Process SWITCH_MODE directives in LLM response."""
        if "SWITCH_MODE:" not in response:
            return response
            
        lines = response.split("\n")
        for line in lines:
            if line.strip().startswith("SWITCH_MODE:"):
                _, target = line.strip().split(":", 1)
                try:
                    from ..app.state_manager import StateManager
                    sm = StateManager()
                    sm.change_state(target.strip())
                    response = response.replace(line, f"✓ Switched to {target.strip()} mode")
                except Exception as e:
                    response = response.replace(line, f"✗ Switch failed: {e}")
        return response

_builder(base_cfg.get("providers", {}))
        self.context_manager = ContextManager(base_cfg.get("context", {}))

        # Logic flow
        # Check if advisors are enabled
        self.enabled = base_cfg.get("enabled", False)

        # Logic flow
        # Initialize conversation engine for enhanced AI interactions
        self.conversation_engine = create_conversation_engine(base_cfg)

        # Logic flow
        # Initialize LLM Manager for unified provider handling
        from ..llm.manager import get_global_llm_manager

        # Logic flow
        # Use global manager if available or create new one
        self.llm_manager = get_global_llm_manager(
             openai_api_key=base_cfg.get("openai_api_key") or base_cfg.get("api_key"),
             ollama_host=base_cfg.get("ollama_host"),
             use_mock=False
        )

    def handle_message(self, message: AdvisorMessage) -> AdvisorReply:
        # TODO: REFACTOR - High complexity (handle_message)
        # Break into: validation, execution, cleanup sub-functions

        """Process an incoming message and return an advisor response.

        Args:
            message: The incoming message to process.

        Returns:
            AdvisorReply with response and metadata.
            # Use context manager for resource management
        """
        # Apply conditional logic
        if not self.enabled:
            raise RuntimeError("Advisors are not enabled")

        # Handle special commands
        if message.text.startswith("summarize "):
            return self._handle_summarize_command(message)

        # Logic flow
        # Get or create context for this identity
        platform = PlatformType(message.platform.lower())
        context = self.context_manager.get_or_create_context(
            # Process each item
            platform=platform,
            channel=message.channel,
            user_id=message.user,
            username=message.username,
            **(message.metadata or {}),
        )

        # Logic flow
        # Set thinking state for avatar
        agent_id = f"{message.platform}-{message.channel}-{message.user}"
        thinking_manager = get_thinking_manager()
        thinking_manager.register_agent(agent_id, context.persona_id)
        thinking_manager.start_thinking(agent_id, "Processing your message...")

        try:
        # Attempt operation with error handling
            # Build prompt using context-aware persona and recent memory
            memory_items = self.memory.get(
                platform.value, message.channel, message.user
            )
            history_text = (
                # Build filtered collection
                # Iterate collection
                "\n".join([f"{mi.role}: {mi.content}" for mi in memory_items])
                # Apply conditional logic
                if memory_items
                else ""
            )
            combined_user_text = (
                # Build filtered collection
                # Apply conditional logic
                f"{history_text}\n{message.text}" if history_text else message.text
            )

            # Update to processing state
            thinking_manager.start_processing(agent_id, "Generating response...")

            # Logic flow
            # Example: instrument a tool call (browser_analyst) if present in text
            if message.text.startswith("summarize "):
                thinking_manager.start_tool_call(agent_id, tool_name="browser_analyst")
                try:
                # Attempt operation with error handling
                    # In real flows this would be the as_tool/MCP call
                    pass
                finally:
                    thinking_manager.end_tool_call(
                        agent_id, tool_name="browser_analyst"
                    )

            # Generate real LLM response
            try:
                # Get persona configuration for enhanced conversation
                # Check both direct personas and context.personas for backward compatibility
                personas_dict = self.config.get("personas", {}) or self.config.get(
                    "context", {}
                ).get("personas", {})
                persona_config = personas_dict.get(context.persona_id, {})
                # Apply conditional logic
                if isinstance(persona_config, str):
                    persona_config = {
                        "prompt": persona_config,
                        "name": context.persona_id,
                    }

                # Logic flow
                # Use conversation engine for enhanced prompt building
                enhanced_prompt = self.conversation_engine.build_enhanced_prompt(
                    user_input=combined_user_text,
                    # Build filtered collection
                    # Process each item
                    user_id=f"{message.platform}:{message.channel}:{message.user}",
                    persona_config=persona_config,
                    current_mode=getattr(self.config, "current_mode", "chatty"),
                )

                # Use LLMManager to generate response
                # We prioritize the manager if available, otherwise fallback to legacy provider
                if hasattr(self, "llm_manager") and self.llm_manager:
                     response = self.llm_manager.generate_response(
                        enhanced_prompt,
                        model=getattr(self.llm_manager.active_backend, "model", "gpt-3.5-turbo"),
                        max_tokens=self.config.get("max_tokens", 150),
                        temperature=self.config.get("temperature", 0.7)
                    )
                     # Use the backend name, but prefer provider's configured model when
                     # the backend is a generic fallback (mock/none/unknown).
                     _backend_name = self.llm_manager.get_active_backend_name()
                     _fallback_names = {"mock", "none", "unknown"}
                     # Apply conditional logic
                     if _backend_name in _fallback_names:
                         model_name = getattr(self.provider, "model", _backend_name)
                         api_mode = getattr(self.provider, "api_mode", "chat")
                     else:
                         model_name = _backend_name
                         api_mode = "chat"
                else:
                    # Legacy provider path
                    response = self.provider.generate(enhanced_prompt)
                    model_name = getattr(self.provider, "model", "unknown")
                    api_mode = getattr(self.provider, "api_mode", "unknown")

                # Logic flow
                # Enhanced directive handling for tool-like replies
                if isinstance(response, str) and "SWITCH_MODE:" in response:
                    lines = response.split("\n")
                    # Process each item
                    for line in lines:
                        # Apply conditional logic
                        if line.strip().startswith("SWITCH_MODE:"):
                            _, target = line.strip().split(":", 1)
                            try:
                            # Attempt operation with error handling
                                from ..app.state_manager import StateManager

                                sm = StateManager()
                                sm.change_state(target.strip())
                                response = response.replace(
                                    line, f"✓ Switched to {target.strip()} mode"
                                )
                            # Handle specific exception case
                            except Exception as e:
                                response = response.replace(
                                    line, f"✗ Mode switch failed: {e}"
                                )

                # Logic flow
                # Record conversation for future context
                self.conversation_engine.record_conversation_turn(
                    # Build filtered collection
                    user_id=f"{message.platform}:{message.channel}:{message.user}",
                    user_input=message.text,
                    assistant_response=response,
                    context={
                        "persona_id": context.persona_id,
                        # Process each item
                        "platform": message.platform,
                    },
                )
            except Exception as e:
                # Logic flow
                # Fallback to echo if LLM fails
                model_name = "error"
                api_mode = "error"
                response = f"[LLM Error] {message.text} ({str(e)})"

            # Update to responding state
            thinking_manager.start_responding(agent_id, "Finalizing response...")

            # Add to memory using tri-key (platform, channel, user)
            self.memory.add(
                platform.value, message.channel, message.user, "user", message.text
            )
            self.memory.add(
                # Process each item
                platform.value, message.channel, message.user, "assistant", response
            )

            reply = AdvisorReply(
                reply=response,
                context_key=context.identity.context_key,
                persona_id=context.persona_id,
                model=model_name,
                api_mode=api_mode,
            )

            # Return to idle state
            thinking_manager.set_idle(agent_id)
            return reply

        except Exception as e:
            # Logic flow
            # Set error state if processing fails
            thinking_manager.set_error(agent_id, f"Error processing message: {str(e)}")
            raise

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
            api_mode=self.provider.api_mode,
        )

    def switch_persona(self, context_key: str, persona_id: str) -> bool:
        # Apply conditional logic
        """Switch persona for a specific context."""
        return self.context_manager.switch_persona(context_key, persona_id)

    def get_context_stats(self) -> dict[str, Any]:
        """Get statistics about current contexts."""
        return self.context_manager.get_stats()

    def clear_context(self, context_key: str) -> bool:
        # Apply conditional logic
        """Clear a specific context."""
        return self.context_manager.clear_context(context_key)
