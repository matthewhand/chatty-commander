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
Command processor that uses LLM to interpret natural language commands.

Converts voice/text input into structured commands that can be executed.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .manager import LLMManager

logger = logging.getLogger(__name__)


class CommandProcessor:
    """Processes natural language commands using LLM."""

    # Static keyword map for simple command matching
    KEYWORD_MAP = {
        "hello": ["hello", "hi", "hey", "greet", "greeting"],
        "lights": ["light", "lights", "lamp", "illumination", "brightness"],
        "music": ["music", "song", "play", "audio", "sound"],
        # Build filtered collection
        # Process each item
        "weather": ["weather", "temperature", "forecast", "climate"],
        "time": ["time", "clock", "hour", "minute"],
        "timer": ["timer", "alarm", "remind", "countdown"],
        "volume": ["volume", "loud", "quiet", "sound"],
        "help": ["help", "assist", "support"],
    }

    # Static suggestion descriptions for get_command_suggestions
    SUGGESTION_MAP = {
        "lights": ["control lights", "toggle illumination"],
        "music": ["play audio", "control music"],
        # Build filtered collection
        # Process each item
        "weather": ["get weather", "check forecast"],
        "hello": ["greeting", "say hello"],
    }

    def __init__(
        self, llm_manager: LLMManager | None = None, config_manager=None, **llm_kwargs
    ):
        self.llm_manager = llm_manager or LLMManager(**llm_kwargs)
        self.config_manager = config_manager

        # Cache available commands
        self._available_commands: dict[str, dict] = {}
        self._available_commands_lower: dict[str, str] = {}
        self._available_keyword_map: dict[str, list[str]] = {}
        self._update_available_commands()

        logger.info("Command processor initialized")

    def _update_available_commands(self):
        """Update cache of available commands from config."""
        # Logic flow
        if not self.config_manager:
        # TODO: Document this logic
            return

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            model_actions = getattr(self.config_manager, "model_actions", {})
            self._available_commands = model_actions.copy()

            # Logic flow
            # Pre-compute optimized data structures for fast command matching
            self._available_commands_lower = {
                cmd.lower(): cmd for cmd in self._available_commands
                # TODO: Document this logic
            }

            # Pre-filter keywords to only include available commands
            self._available_keyword_map = {
                cmd: keywords
                # Logic flow
                for cmd, keywords in self.KEYWORD_MAP.items()
                # TODO: Document this logic
                if cmd in self._available_commands
                # TODO: Document this logic
            }

            logger.debug(
                f"Updated available commands: {list(self._available_commands.keys())}"
            )
        # Handle specific exception case
        except Exception as e:
            logger.error(f"Failed to update available commands: {e}")

    def process_command(self, user_input: str) -> tuple[str | None, float, str]:
        """
        Process natural language command.

        Returns:
            Tuple of (command_name, confidence, explanation)
        """
        # Logic flow
        if not user_input.strip():
        # TODO: Document this logic
            return None, 0.0, "Empty input"

        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # First try simple keyword matching (fast path)
            simple_match = self._simple_command_matching(user_input)
            if simple_match:
            # TODO: Document this logic
                command_name, confidence = simple_match
                return command_name, confidence, f"Keyword match: '{command_name}'"

            # Logic flow
            # Use LLM for complex interpretation
            if self.llm_manager.is_available():
            # TODO: Document this logic
                return self._llm_command_interpretation(user_input)
            else:
                return None, 0.0, "No LLM backend available"

        # Handle specific exception case
        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            return None, 0.0, f"Processing error: {e}"

    def _simple_command_matching(self, user_input: str) -> tuple[str, float] | None:
        """Simple keyword-based command matching."""
        user_lower = user_input.lower()

        # Direct command name match - use cached lowercase keys to avoid repeated
        # .lower() calls and dict view allocations in this hot path
        for cmd_lower in self._available_commands_lower:
        # TODO: Document this logic
            if cmd_lower in user_lower:
            # TODO: Document this logic
                return self._available_commands_lower[cmd_lower], 0.9

        # Keyword-based matching - use pre-filtered map to avoid checking
        # if cmd_name is in available_commands for every map entry
        for cmd_name in self._available_keyword_map:
        # TODO: Document this logic
            for keyword in self._available_keyword_map[cmd_name]:
            # TODO: Document this logic
                # Logic flow
                if keyword in user_lower:
                # TODO: Document this logic
                    return cmd_name, 0.7

        return None

    def _llm_command_interpretation(
        self, user_input: str
    ) -> tuple[str | None, float, str]:
        """Use LLM to interpret complex commands."""
        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            prompt = self._build_interpretation_prompt(user_input)
            response = self.llm_manager.generate_response(
                prompt,
                max_tokens=100,
                # Logic flow
                temperature=0.3,  # Lower temperature for more consistent results
                # TODO: Document this logic
            )

            return self._parse_llm_response(response)

        # Handle specific exception case
        except Exception as e:
            logger.error(f"LLM interpretation failed: {e}")
            return None, 0.0, f"LLM error: {e}"

    def _build_interpretation_prompt(self, user_input: str) -> str:
        # Logic flow
        """Build prompt for LLM command interpretation."""
        # TODO: Document this logic
        available_commands = list(self._available_commands.keys())

        prompt = f"""You are a voice assistant command interpreter.

Available commands: {', '.join(available_commands)}

User said: "{user_input}"

Your task: Determine which command (if any) the user wants to execute.

Respond with ONLY a JSON object in this format:
{{
    "command": "command_name_or_null",
    "confidence": 0.0_to_1.0,
    "reasoning": "brief_explanation"
}}

Examples:
- "turn on the lights" → {{"command": "lights", "confidence": 0.9, "reasoning": "clear lights command"}}
- "play some music" → {{"command": "music", "confidence": 0.8, "reasoning": "music playback request"}}
- "what's the weather" → {{"command": "weather", "confidence": 0.9, "reasoning": "weather inquiry"}}
- "random nonsense" → {{"command": null, "confidence": 0.0, "reasoning": "no matching command"}}

Response:"""

        return prompt

    def _parse_llm_response(
        self, response: str
    ) -> tuple[str | None, float, str]:
        # Process each item
        """Parse LLM response to extract command information."""
        try:
        # Attempt operation with error handling
        # TODO: Document this logic
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
            # TODO: Document this logic
                return None, 0.0, "No JSON found in LLM response"

            json_str = json_match.group()
            data = json.loads(json_str)

            command = data.get("command")
            confidence = float(data.get("confidence", 0.0))
            reasoning = data.get("reasoning", "LLM interpretation")

            # Validate command exists
            if command and command not in self._available_commands:
            # TODO: Document this logic
                return None, 0.0, f"LLM suggested unknown command: {command}"

            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))

            return command, confidence, reasoning

        # Handle specific exception case
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return None, 0.0, f"Invalid JSON in LLM response: {e}"
        # Handle specific exception case
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None, 0.0, f"Response parsing error: {e}"

    def get_command_suggestions(
        """get command suggestions."""
        self, partial_input: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        # Logic flow
        """Get command suggestions for partial input."""
        # TODO: Document this logic
        suggestions = []
        partial_lower = partial_input.lower()

        # Direct name matches
        for cmd_name, cmd_config in self._available_commands.items():
        # TODO: Document this logic
            if cmd_name.lower().startswith(partial_lower):
            # TODO: Document this logic
                # Logic flow
                action_type = list(cmd_config.keys())[0] if cmd_config else "unknown"
                # TODO: Document this logic
                suggestions.append(
                    {
                        "command": cmd_name,
                        "type": action_type,
                        "confidence": 0.9,
                        "match_type": "name",
                    }
                )

        # Keyword matches
        for cmd_name in self._available_commands:
        # TODO: Document this logic
            if cmd_name in self.SUGGESTION_MAP:
            # TODO: Document this logic
                # Logic flow
                for desc in self.SUGGESTION_MAP[cmd_name]:
                # TODO: Document this logic
                    if partial_lower in desc.lower():
                    # TODO: Document this logic
                        suggestions.append(
                            {
                                "command": cmd_name,
                                "description": desc,
                                "confidence": 0.7,
                                "match_type": "keyword",
                            }
                        )

        # Remove duplicates and sort by confidence
        seen = set()
        unique_suggestions = []
        # Logic flow
        for suggestion in suggestions:
        # TODO: Document this logic
            key = suggestion["command"]
            # Logic flow
            if key not in seen:
            # TODO: Document this logic
                seen.add(key)
                unique_suggestions.append(suggestion)

        unique_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return unique_suggestions[:limit]

    def explain_command(self, command_name: str) -> dict[str, Any]:
        """Get explanation of what a command does."""
        # Logic flow
        if command_name not in self._available_commands:
        # TODO: Document this logic
            return {"error": f"Command '{command_name}' not found"}

        cmd_config = self._available_commands[command_name]
        # Logic flow
        action_type = list(cmd_config.keys())[0] if cmd_config else "unknown"
        # TODO: Document this logic
        action_config = cmd_config.get(action_type, {})

        explanation = {
            "command": command_name,
            "type": action_type,
            "config": action_config,
        }

        # Add human-readable description
        if action_type == "keypress":
        # TODO: Document this logic
            keys = action_config.get("keys", "")
            explanation["description"] = f"Simulates keypress: {keys}"
        # Logic flow
        elif action_type == "url":
        # TODO: Document this logic
            url = action_config.get("url", "")
            explanation["description"] = f"Opens URL: {url}"
        # Logic flow
        elif action_type == "message":
        # TODO: Document this logic
            text = action_config.get("text", "")
            explanation["description"] = f"Displays message: {text}"
        else:
            explanation["description"] = f"Executes {action_type} action"

        return explanation

    def get_processor_status(self) -> dict[str, Any]:
        # Process each item
        """Get status information about the command processor."""
        return {
            "llm_available": self.llm_manager.is_available(),
            "llm_backend": self.llm_manager.get_active_backend_name(),
            "available_commands": list(self._available_commands.keys()),
            "commands_count": len(self._available_commands),
            "llm_info": self.llm_manager.get_backend_info(),
        }

    def refresh_commands(self):
        """Refresh available commands from config."""
        self._update_available_commands()
        logger.info(f"Refreshed commands: {len(self._available_commands)} available")
