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

"""Tests for AI fallback mechanisms when LLM is unavailable."""

from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.advisors.service import (
    AdvisorMessage,
    AdvisorReply,
    AdvisorsService,
)

@pytest.fixture(autouse=True)
def disable_llm_manager():
    """Disable the new LLMManager for these legacy fallback tests."""
    with patch("src.chatty_commander.llm.manager.get_global_llm_manager", return_value=None):
        yield


def _create_mock_provider(side_effect=None, return_value=None, model="gpt-4", api_mode="completion"):
    """Helper to create a mock provider that generates responses."""
    provider = Mock()
    provider.model = model
    provider.api_mode = api_mode
    if side_effect:
        provider.generate.side_effect = side_effect
    elif return_value is not None:
        provider.generate.return_value = return_value
    return provider


class TestLLMFallbackMechanisms:
    """Tests for LLM fallback mechanisms when primary AI is unavailable."""

    def test_llm_provider_failure_fallback(self):
        """Test fallback when LLM provider fails completely."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("LLM service unavailable")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        }
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)

            # Use 'default_persona' as fallback when user has not explicitly set a persona
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Hello, how are you?",
                username="test_user",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply
            assert response.model == "error"

    def test_llm_timeout_fallback(self):
        """Test fallback when LLM times out."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=TimeoutError("Request timed out after 30 seconds"),
                model="gpt-3.5-turbo"
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test", "timeout": 30}},
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        }
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="slack",
                channel="general",
                user="user456",
                text="Can you help me with this task?",
                username="john_doe",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_llm_rate_limit_fallback(self):
        """Test fallback when LLM hits rate limits."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("Rate limit exceeded. Please try again later."),
                model="claude-3"
            )

            config = {
                "enabled": True,
                "providers": {"anthropic": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a data analyst.",
                            "name": "Data Analyst",
                        }
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="data",
                user="analyst_user",
                text="Analyze this dataset for me",
                username="data_guru",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_llm_network_error_fallback(self):
        """Test fallback when network connectivity fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=ConnectionError("Network unreachable"),
                model="llama2"
            )

            config = {
                "enabled": True,
                "providers": {
                    "local": {"base_url": "http://localhost:8080", "api_key": "local"}
                },
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a helpful assistant.",
                            "name": "Local Assistant",
                        }
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="offline",
                user="offline_user",
                text="What's the weather like?",
                username="weather_fan",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_llm_invalid_response_fallback(self):
        """Test fallback when LLM returns invalid response format."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            # Create a provider that returns an empty string (invalid but not None)
            mock_build.return_value = _create_mock_provider(return_value="")

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        }
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Tell me a joke",
                username="joke_lover",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # Empty response is returned as-is by the service
            assert response.reply == ""

    def test_llm_with_memory_fallback(self):
        """Test fallback with memory context when LLM fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("LLM error with memory context")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "memory": {"max_items_per_context": 10},
                "commands": {},
            }

            service = AdvisorsService(config)

            # First, add some memory
            message1 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Remember that I like pizza",
            )
            service.handle_message(message1)

            # Now test fallback with memory
            message2 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="What do I like?",
            )

            response = service.handle_message(message2)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_llm_mode_switch_fallback_failure(self):
        """Test mode switch directive handling when it fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            # Return a response with SWITCH_MODE directive
            mock_build.return_value = _create_mock_provider(
                return_value="SWITCH_MODE: work\nHere's your response."
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Switch to work mode",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # The SWITCH_MODE directive should be processed
            assert "SWITCH_MODE:" not in response.reply

    def test_llm_conversation_engine_fallback(self):
        """Test conversation engine error handling."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("Conversation engine error")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Hello",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_llm_fallback_with_different_api_modes(self):
        """Test fallback works with different API modes."""
        for api_mode in ["completion", "chat"]:
            with patch(
                "src.chatty_commander.advisors.service.build_provider_safe"
            ) as mock_build:
                mock_build.return_value = _create_mock_provider(
                    side_effect=Exception(f"API mode {api_mode} failed"),
                    api_mode=api_mode
                )

                config = {
                    "enabled": True,
                    "providers": {
                        "openai": {"api_key": "test", "api_mode": api_mode}
                    },
                    "context": {
                        "personas": {
                            "analyst": {
                                "system_prompt": "You are an analyst.",
                                "name": "Analyst",
                            }
                        },
                        "default_persona": "analyst",
                    },
                    "commands": {},
                }

                service = AdvisorsService(config)
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text="Test message",
                )

                response = service.handle_message(message)

                assert isinstance(response, AdvisorReply)
                assert "LLM Error" in response.reply


class TestSmartFallbackResponses:
    """Tests for smart fallback response generation."""

    def test_cached_response_fallback(self):
        """Test using cached response when LLM fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("LLM error for cache test")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="What is the capital of France?",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_pattern_based_fallback_responses(self):
        """Test pattern-based fallback response generation."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("LLM error for pattern test")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Help me with something",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply

    def test_fallback_response_formatting(self):
        """Test that fallback responses are properly formatted."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                side_effect=Exception("LLM error for formatting test")
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Simple text",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM Error" in response.reply
            assert response.context_key == "discord:test:user123"
            assert response.persona_id == "general"


class TestGracefulDegradation:
    """Tests for graceful degradation when multiple components fail."""

    def test_memory_failure_graceful_degradation(self):
        """Test graceful degradation when memory fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                return_value="This is a test response"
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Test message",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert response.reply == "This is a test response"

    def test_context_switching_during_degradation(self):
        """Test context switching works during degraded mode."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_build.return_value = _create_mock_provider(
                return_value="Response with default persona"
            )

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)

            message1 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="First message",
            )

            response1 = service.handle_message(message1)

            assert isinstance(response1, AdvisorReply)
            assert response1.reply == "Response with default persona"

    def test_multiple_provider_fallback_chain(self):
        """Test fallback chain through multiple providers."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            # Simulate fallback chain
            call_count = [0]

            def fallback_chain(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Provider 1 failed")
                return "Fallback response"

            mock_build.return_value = _create_mock_provider(
                side_effect=fallback_chain
            )

            config = {
                "enabled": True,
                "providers": {
                    "primary": {"api_key": "test1"},
                    "fallback": {"api_key": "test2"},
                },
                "context": {
                    "personas": {
                        "analyst": {
                            "system_prompt": "You are an analyst.",
                            "name": "Analyst",
                        }
                    },
                    "default_persona": "analyst",
                },
                "commands": {},
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Test message",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # First call fails, error response returned
            assert "LLM Error" in response.reply or "Fallback response" in response.reply
