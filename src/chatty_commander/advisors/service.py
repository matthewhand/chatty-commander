from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from chatty_commander.tools.browser_analyst import AnalystRequest, summarize_url
from .memory import MemoryStore
from .providers import build_provider
from .prompting import Persona, build_provider_prompt

@dataclass
class AdvisorMessage:
    platform: str
    channel: str
    user: str
    text: str
    meta: dict[str, Any] | None = None


@dataclass
class AdvisorReply:
    text: str
    meta: dict[str, Any] | None = None


class AdvisorsService:
    """Thin facade for the advisor core (openai-agents based).

    MVP provides a simple echo pipeline and pluggable LLM/tool calls later.
    """

    def __init__(
        self,
        *,
        config: Any,
        send_reply: Optional[Callable[[AdvisorReply, AdvisorMessage], None]] = None,
    ) -> None:
        self.config = config
        self.send_reply = send_reply

        self.enabled: bool = bool(getattr(config, "advisors", {}).get("enabled", False))
        self.llm_api_mode: str = getattr(config, "advisors", {}).get("llm_api_mode", "completion")
        self.model: str = getattr(config, "advisors", {}).get("model", "gpt-oss20b")
        self.features: dict[str, Any] = getattr(config, "advisors", {}).get("features", {})
        mem_cfg = getattr(config, "advisors", {}).get("memory", {})
        self.memory = MemoryStore(
            max_items_per_context=200,
            persist=bool(mem_cfg.get("persistence_enabled", False)),
            persist_path=mem_cfg.get("persistence_path"),
        )
        self.provider = build_provider(config)
        personas = getattr(config, "advisors", {}).get("personas", {})
        self.persona_name: str = personas.get("default", "default")
        self.persona = Persona(
            name=self.persona_name,
            system=(
                "Provide helpful, concise answers."
                if self.persona_name == "default"
                else f"Persona {self.persona_name}: provide helpful, concise answers."
            ),
        )

    def handle_message(self, message: AdvisorMessage) -> AdvisorReply:
        """Handle a message. MVP: echo with a prefix to verify wiring."""
        if not self.enabled:
            return AdvisorReply(text="[advisors disabled]")

        # Minimal tool invocation: summarize URL if feature enabled and pattern matches
        if self.features.get("browser_analyst") and message.text.lower().startswith("summarize"):
            # Accept formats: "summarize URL" or "summarize: URL"
            parts = message.text.split(None, 1)
            url = ""
            if len(parts) == 2:
                url = parts[1].strip().lstrip(":").strip()
            if url:
                result = summarize_url(AnalystRequest(url=url))
                reply_text = f"(advisor:{self.model}/{self.llm_api_mode}) summary: {result.title}"
                reply = AdvisorReply(text=reply_text, meta={"summary": result.summary, "url": result.url})
                self.memory.add(message.platform, message.channel, message.user, "user", message.text)
                self.memory.add(message.platform, message.channel, message.user, "assistant", reply.text)
                if self.send_reply:
                    try:
                        self.send_reply(reply, message)
                    except Exception:
                        pass
                return reply

        # Default echo w/ provider hint and persona tag (if set)
        # Demonstrate prompt build (stubbed) and provider hint
        _prompt = build_provider_prompt(self.llm_api_mode, self.persona, message.text)
        provider_hint = self.provider.generate("")
        persona_tag = f" [persona:{self.persona_name}]" if self.persona_name != "default" else ""
        reply_text = f"(advisor:{self.model}/{self.llm_api_mode}) {message.text}{persona_tag} [{provider_hint}]"
        reply = AdvisorReply(text=reply_text)
        self.memory.add(message.platform, message.channel, message.user, "user", message.text)
        self.memory.add(message.platform, message.channel, message.user, "assistant", reply.text)
        if self.send_reply:
            try:
                self.send_reply(reply, message)
            except Exception:
                pass
        return reply


