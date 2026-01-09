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

    def __init__(
        self, llm_manager: LLMManager | None = None, config_manager=None, **llm_kwargs
    ):
        self.llm_manager = llm_manager or LLMManager(**llm_kwargs)
        self.config_manager = config_manager

        # Cache available commands
        self._available_commands: dict[str, dict] = {}
        self._update_available_commands()

        logger.info("Command processor initialized")

    def _update_available_commands(self):
        """Update cache of available commands from config."""
        if not self.config_manager:
            return

        try:
            model_actions = getattr(self.config_manager, "model_actions", {})
            self._available_commands = model_actions.copy()
            logger.debug(
                f"Updated available commands: {list(self._available_commands.keys())}"
            )
        except Exception as e:
            logger.error(f"Failed to update available commands: {e}")

    def process_command(self, user_input: str) -> tuple[str | None, float, str]:
        """
        Process natural language command.

        Returns:
            Tuple of (command_name, confidence, explanation)
        """
        if not user_input.strip():
            return None, 0.0, "Empty input"

        try:
            # First try simple keyword matching (fast path)
            simple_match = self._simple_command_matching(user_input)
            if simple_match:
                command_name, confidence = simple_match
                return command_name, confidence, f"Keyword match: '{command_name}'"

            # Use LLM for complex interpretation
            if self.llm_manager.is_available():
                return self._llm_command_interpretation(user_input)
            else:
                return None, 0.0, "No LLM backend available"

        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            return None, 0.0, f"Processing error: {e}"

    def _simple_command_matching(self, user_input: str) -> tuple[str, float] | None:
        """Simple keyword-based command matching."""
        user_lower = user_input.lower()

        # Direct command name match
        for cmd_name in self._available_commands.keys():
            if cmd_name.lower() in user_lower:
                return cmd_name, 0.9

        # Keyword-based matching
        keyword_map = {
            "hello": ["hello", "hi", "hey", "greet", "greeting"],
            "lights": ["light", "lights", "lamp", "illumination", "brightness"],
            "music": ["music", "song", "play", "audio", "sound"],
            "weather": ["weather", "temperature", "forecast", "climate"],
            "time": ["time", "clock", "hour", "minute"],
            "timer": ["timer", "alarm", "remind", "countdown"],
            "volume": ["volume", "loud", "quiet", "sound"],
            "help": ["help", "assist", "support"],
        }

        for cmd_name, keywords in keyword_map.items():
            if cmd_name in self._available_commands:
                for keyword in keywords:
                    if keyword in user_lower:
                        return cmd_name, 0.7

        return None

    def _llm_command_interpretation(
        self, user_input: str
    ) -> tuple[str | None, float, str]:
        """Use LLM to interpret complex commands."""
        try:
            prompt = self._build_interpretation_prompt(user_input)
            response = self.llm_manager.generate_response(
                prompt,
                max_tokens=100,
                temperature=0.3,  # Lower temperature for more consistent results
            )

            return self._parse_llm_response(response, user_input)

        except Exception as e:
            logger.error(f"LLM interpretation failed: {e}")
            return None, 0.0, f"LLM error: {e}"

    def _build_interpretation_prompt(self, user_input: str) -> str:
        """Build prompt for LLM command interpretation."""
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
        """Parse LLM response to extract command information."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                return None, 0.0, "No JSON found in LLM response"

            json_str = json_match.group()
            data = json.loads(json_str)

            command = data.get("command")
            confidence = float(data.get("confidence", 0.0))
            reasoning = data.get("reasoning", "LLM interpretation")

            # Validate command exists
            if command and command not in self._available_commands:
                return None, 0.0, f"LLM suggested unknown command: {command}"

            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))

            return command, confidence, reasoning

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return None, 0.0, f"Invalid JSON in LLM response: {e}"
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None, 0.0, f"Response parsing error: {e}"

    def get_command_suggestions(
        self, partial_input: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get command suggestions for partial input."""
        suggestions = []
        partial_lower = partial_input.lower()

        # Direct name matches
        for cmd_name, cmd_config in self._available_commands.items():
            if cmd_name.lower().startswith(partial_lower):
                action_type = list(cmd_config.keys())[0] if cmd_config else "unknown"
                suggestions.append(
                    {
                        "command": cmd_name,
                        "type": action_type,
                        "confidence": 0.9,
                        "match_type": "name",
                    }
                )

        # Keyword matches
        keyword_map = {
            "lights": ["control lights", "toggle illumination"],
            "music": ["play audio", "control music"],
            "weather": ["get weather", "check forecast"],
            "hello": ["greeting", "say hello"],
        }

        for cmd_name in self._available_commands.keys():
            if cmd_name in keyword_map:
                for desc in keyword_map[cmd_name]:
                    if partial_lower in desc.lower():
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
        for suggestion in suggestions:
            key = suggestion["command"]
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        unique_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return unique_suggestions[:limit]

    def explain_command(self, command_name: str) -> dict[str, Any]:
        """Get explanation of what a command does."""
        if command_name not in self._available_commands:
            return {"error": f"Command '{command_name}' not found"}

        cmd_config = self._available_commands[command_name]
        action_type = list(cmd_config.keys())[0] if cmd_config else "unknown"
        action_config = cmd_config.get(action_type, {})

        explanation = {
            "command": command_name,
            "type": action_type,
            "config": action_config,
        }

        # Add human-readable description
        if action_type == "keypress":
            keys = action_config.get("keys", "")
            explanation["description"] = f"Simulates keypress: {keys}"
        elif action_type == "url":
            url = action_config.get("url", "")
            explanation["description"] = f"Opens URL: {url}"
        elif action_type == "message":
            text = action_config.get("text", "")
            explanation["description"] = f"Displays message: {text}"
        else:
            explanation["description"] = f"Executes {action_type} action"

        return explanation

    def get_processor_status(self) -> dict[str, Any]:
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
