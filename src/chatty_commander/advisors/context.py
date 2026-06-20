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
Tab-aware context switching for advisors.

This module manages persistent identity and context switching across different
applications, allowing advisors to maintain appropriate personas and memory
per application/tab context.
"""

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class PlatformType(Enum):
    """Supported platform types for context switching."""

    DISCORD = "discord"
    SLACK = "slack"
    WEB = "web"
    CLI = "cli"
    GUI = "gui"


@dataclass
class ContextIdentity:
    """Represents a user's identity in a specific context."""

    platform: PlatformType
    channel: str
    user_id: str
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    created_at: float | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    @property
    def context_key(self) -> str:
        """Generate a unique context key for this identity."""
        return f"{self.platform.value}:{self.channel}:{self.user_id}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["platform"] = self.platform.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextIdentity":
        """Create from dictionary."""
        data["platform"] = PlatformType(data["platform"])
        return cls(**data)


@dataclass
class ContextState:
    """Represents the current state of a context."""

    identity: ContextIdentity
    persona_id: str
    system_prompt: str
    memory_key: str
    metadata: dict[str, Any]
    last_activity: float | None = None

    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["identity"] = self.identity.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextState":
        """Create from dictionary."""
        data["identity"] = ContextIdentity.from_dict(data["identity"])
        return cls(**data)


class ContextManager:
    """
    Manages tab-aware context switching for advisors.

    This class handles:
    - Persistent identity tracking across applications
    - Context-aware persona switching
    - Memory isolation per context
    - State persistence and recovery
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize context manager."""
        self.config = config
        self.contexts: dict[str, ContextState] = {}

        # Support both direct 'personas' key or nested under 'context'
        personas_dict = config.get("personas", {}) or config.get("context", {}).get("personas", {})
        self.personas: dict[str, dict[str, Any]] = personas_dict

        self.default_persona: str = config.get("default_persona") or config.get("context", {}).get("default_persona", "general")

        # Persistence settings
        self.persistence_enabled = config.get("persistence_enabled", True)
        self.persistence_path = Path(
            config.get("persistence_path", "data/contexts.json")
        )

        # Save debounce: re-serializing the entire context dict on every message
        # is wasteful. Instead, save only after a number of changes accumulate or
        # after a short interval elapses (whichever comes first). ``_last_save_time``
        # starts at 0.0 so the first change always persists.
        self._save_every = max(1, int(config.get("save_every_changes", 25)))
        self._save_interval = float(config.get("save_interval_seconds", 5.0))
        self._changes_since_save = 0
        self._last_save_time = 0.0

        # Opportunistic expiry of inactive contexts on access, gated by a counter
        # so it does not run on every call.
        self._inactive_max_age_hours = float(
            config.get("inactive_max_age_hours", 24.0)
        )
        self._expire_every = max(1, int(config.get("expire_every_accesses", 100)))
        self._accesses_since_expire = 0

        # Load existing contexts
        if self.persistence_enabled:
            self._load_contexts()

    def get_or_create_context(
        self,
        platform: PlatformType,
        channel: str,
        user_id: str,
        username: str | None = None,
        **kwargs,
    ) -> ContextState:
        """
        Get existing context or create new one for the given identity.

        Args:
            platform: The platform type (Discord, Slack, etc.)
            channel: Channel or conversation ID
            user_id: Unique user identifier
            username: Optional username for display
            **kwargs: Additional identity metadata

        Returns:
            ContextState for the identity
        """
        self._maybe_expire_inactive()

        identity = ContextIdentity(
            platform=platform,
            channel=channel,
            user_id=user_id,
            username=username,
            **kwargs,
        )

        context_key = identity.context_key

        if context_key not in self.contexts:
            # Create new context
            persona_id = self._resolve_persona_for_context(identity)
            system_prompt = self.personas.get(persona_id, {}).get("system_prompt", "")
            memory_key = f"{context_key}:memory"

            context = ContextState(
                identity=identity,
                persona_id=persona_id,
                system_prompt=system_prompt,
                memory_key=memory_key,
                last_activity=time.time(),
                metadata={},
            )

            self.contexts[context_key] = context

            if self.persistence_enabled:
                self._maybe_save()

        else:
            # Update existing context
            context = self.contexts[context_key]
            context.last_activity = time.time()

            # Update identity if new info provided
            if username and username != context.identity.username:
                context.identity.username = username

            if self.persistence_enabled:
                self._maybe_save()

        return self.contexts[context_key]

    def switch_persona(self, context_key: str, persona_id: str) -> bool:
        """
        Switch the persona for a specific context.

        Args:
            context_key: The context to switch
            persona_id: New persona ID

        Returns:
            True if switch successful, False if persona not found
        """
        if context_key not in self.contexts:
            return False

        if persona_id not in self.personas:
            return False

        context = self.contexts[context_key]
        context.persona_id = persona_id
        context.system_prompt = self.personas[persona_id].get("system_prompt", "")
        context.last_activity = time.time()

        if self.persistence_enabled:
            self._save_contexts()

        return True

    def get_context(self, context_key: str) -> ContextState | None:
        """
        Switch the persona for a specific context.

        Args:
        context_key: The context to switch
        persona_id: New persona ID

        Returns:
        True if switch successful, False if persona not found
        """
        """Get context by key."""
        return self.contexts.get(context_key)

    def list_contexts(self) -> list[ContextState]:
        return list(self.contexts.values())

    def clear_context(self, context_key: str) -> bool:
        """
        Clear a specific context.

        Args:
            context_key: The context to clear

        Returns:
            True if context was cleared, False if not found
        """
        if context_key not in self.contexts:
            return False

        del self.contexts[context_key]

        if self.persistence_enabled:
            self._save_contexts()

        return True

    def clear_inactive_contexts(self, max_age_hours: float = 24.0) -> int:
        """
        Clear contexts that haven't been active for the specified time.

        Args:
            max_age_hours: Maximum age in hours before clearing

        Returns:
            Number of contexts cleared
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        to_clear = []
        for context_key, context in list(self.contexts.items()):
            # last_activity is set in __post_init__, guaranteed non-None after initialization
            if context.last_activity is None:
                continue
            if current_time - context.last_activity > max_age_seconds:
                to_clear.append(context_key)

        for context_key in to_clear:
            del self.contexts[context_key]

        if to_clear and self.persistence_enabled:
            self._save_contexts()

        return len(to_clear)

    def _maybe_expire_inactive(self) -> None:
        """Opportunistically expire inactive contexts, gated by an access counter.

        Avoids unbounded growth of the in-memory (and persisted) context dict
        without scanning on every single access.
        """
        self._accesses_since_expire += 1
        if self._accesses_since_expire >= self._expire_every:
            self._accesses_since_expire = 0
            self.clear_inactive_contexts(self._inactive_max_age_hours)

    def _maybe_save(self) -> None:
        """Debounced save: persist only after enough changes or time elapsed.

        Re-serializing the entire context dict on every message is expensive.
        This flushes when ``_save_every`` changes have accumulated or when
        ``_save_interval`` seconds have passed since the last save (whichever
        comes first). The first change always persists because ``_last_save_time``
        starts at 0.0.
        """
        if not self.persistence_enabled:
            return

        self._changes_since_save += 1
        now = time.time()
        if (
            self._changes_since_save >= self._save_every
            or (now - self._last_save_time) >= self._save_interval
        ):
            self._save_contexts()

    def _resolve_persona_for_context(self, identity: ContextIdentity) -> str:
        """
        Resolve which persona to use for a given context.

        This can be extended to implement more sophisticated persona
        selection logic based on platform, channel, user, etc.
        """
        # Simple logic: use platform-specific persona if available
        platform_persona = f"{identity.platform.value}_default"

        if platform_persona in self.personas:
            return platform_persona

        # If the platform itself is defined as a persona, use it
        if identity.platform.value in self.personas:
            return identity.platform.value

        # Fall back to default persona
        return self.default_persona

    def _load_contexts(self) -> None:
        """Load contexts from persistence file."""
        if not self.persistence_path.exists():
            return

        try:
            with open(self.persistence_path) as f:
                data = json.load(f)

            for context_key, context_data in data.items():
                try:
                    context = ContextState.from_dict(context_data)
                    self.contexts[context_key] = context
                except Exception:
                    # Skip invalid contexts
                    continue

        except Exception:
            # Log error but continue
            pass

    def _save_contexts(self) -> None:
        """Save contexts to persistence file using an atomic write.

        Writes to a temporary file in the same directory and then atomically
        replaces the target via os.replace(). This prevents a corrupted or
        partially written file if the process is interrupted mid-write or if
        multiple saves race; the target file always reflects a complete state.
        """
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for context_key, context in self.contexts.items():
            data[context_key] = context.to_dict()

        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.persistence_path.parent),
            prefix=self.persistence_path.name,
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.persistence_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        # Reset debounce bookkeeping now that disk reflects current state.
        self._changes_since_save = 0
        self._last_save_time = time.time()

    def flush(self) -> None:
        """Force any pending debounced changes to disk (e.g. on shutdown)."""
        if self.persistence_enabled and self._changes_since_save:
            self._save_contexts()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about current contexts."""
        platform_counts: dict[str, int] = {}
        persona_counts: dict[str, int] = {}

        for context in self.contexts.values():
            platform = context.identity.platform.value
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

            persona_counts[context.persona_id] = (
                persona_counts.get(context.persona_id, 0) + 1
            )

        return {
            "total_contexts": len(self.contexts),
            "platform_distribution": platform_counts,
            "persona_distribution": persona_counts,
            "persistence_enabled": self.persistence_enabled,
            "persistence_path": str(self.persistence_path),
        }
