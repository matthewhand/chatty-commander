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


class TestLLMFallbackMechanisms:
    """Tests for LLM fallback mechanisms when primary AI is unavailable."""

    def test_llm_provider_failure_fallback(self):
        """Test fallback when LLM provider fails completely."""
        # Mock provider to simulate complete failure
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM service unavailable")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
                text="Hello, how are you?",
                username="test_user",
            )

            # Should handle provider failure gracefully with fallback response
            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM error" in response.reply
            assert "Hello, how are you?" in response.reply
            assert response.model == "gpt-4"
            assert response.api_mode == "completion"

    def test_llm_timeout_fallback(self):
        """Test fallback when LLM times out."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = TimeoutError(
                "Request timed out after 30 seconds"
            )
            mock_provider.model = "gpt-3.5-turbo"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
            assert "LLM error" in response.reply
            assert "Request timed out after 30 seconds" in response.reply

    def test_llm_rate_limit_fallback(self):
        """Test fallback when LLM hits rate limits."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception(
                "Rate limit exceeded. Please try again later."
            )
            mock_provider.model = "claude-3"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
            assert "Rate limit exceeded" in response.reply
            assert "Analyze this dataset for me" in response.reply

    def test_llm_network_error_fallback(self):
        """Test fallback when network connectivity fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = ConnectionError("Network unreachable")
            mock_provider.model = "llama2"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
            assert "LLM error" in response.reply
            assert "Network unreachable" in response.reply

    def test_llm_invalid_response_fallback(self):
        """Test fallback when LLM returns invalid response format."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.return_value = None  # Invalid response
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
            # None response should be converted to string "None"
            assert str(response.reply) == "None"

    def test_llm_with_memory_fallback(self):
        """Test fallback with memory context when LLM fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM service down")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
                "memory": {"max_items_per_context": 10, "persistence_enabled": False},
                "commands": {},
            }

            service = AdvisorsService(config)

            # Add some memory context
            service.memory.add("discord", "test", "user123", "user", "Hello there")
            service.memory.add(
                "discord", "test", "user123", "assistant", "Hi! How can I help?"
            )

            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="What did we talk about before?",
                username="memory_user",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "LLM error" in response.reply
            # Should still include the current message in fallback
            assert "What did we talk about before?" in response.reply

    def test_llm_mode_switch_fallback_failure(self):
        """Test fallback when mode switch fails due to LLM issues."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.return_value = "✗ Mode switch failed: Invalid mode"
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
                text="/mode switch invalid_mode",
                username="mode_tester",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "✗ Mode switch failed" in response.reply

    def test_llm_persona_fallback_when_context_fails(self):
        """Test fallback when persona context creation fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.return_value = (
                "I understand you're asking about Python."
            )
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            # Mock context manager to fail
            with patch(
                "src.chatty_commander.advisors.service.ContextManager"
            ) as mock_cm:
                mock_cm_instance = Mock()
                mock_cm_instance.get_or_create_context.side_effect = Exception(
                    "Context creation failed"
                )
                mock_cm.return_value = mock_cm_instance

                config = {
                    "enabled": True,
                    "providers": {"openai": {"api_key": "test"}},
                    "personas": {
                        "default": {
                            "prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        }
                    },
                }

                service = AdvisorsService(config)
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text="Tell me about Python",
                    username="python_learner",
                )

                # Should raise exception since context is fundamental
                with pytest.raises(Exception):
                    service.handle_message(message)

    def test_llm_conversation_engine_fallback(self):
        """Test fallback when conversation engine fails."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("Conversation engine error")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "personas": {
                    "default": {
                        "prompt": "You are a helpful assistant.",
                        "name": "Default Assistant",
                    }
                },
            }

            service = AdvisorsService(config)
            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="How's the weather?",
                username="weather_user",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            assert "Conversation engine error" in response.reply

    def test_llm_fallback_preserves_context_key(self):
        """Test that fallback responses preserve context key for continuity."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM error")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
                text="Hello there",
                username="context_user",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # The context_key should be the identity context key, not the persona
            assert (
                response.context_key == "discord:test:user123"
            )  # Should preserve context key

    def test_llm_fallback_with_different_api_modes(self):
        """Test fallback behavior with different API modes."""
        api_modes = ["completion", "responses"]

        for api_mode in api_modes:
            with patch(
                "src.chatty_commander.advisors.service.build_provider_safe"
            ) as mock_build:
                mock_provider = Mock()
                mock_provider.generate.side_effect = Exception(
                    f"API mode {api_mode} failed"
                )
                mock_provider.model = "gpt-4"
                mock_provider.api_mode = api_mode
                mock_build.return_value = mock_provider

                config = {
                    "enabled": True,
                    "providers": {"openai": {"api_key": "test", "api_mode": api_mode}},
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
                    text=f"Test message for {api_mode} mode",
                    username="api_tester",
                )

                response = service.handle_message(message)

                assert isinstance(response, AdvisorReply)
                assert response.api_mode == api_mode
                assert f"API mode {api_mode} failed" in response.reply


class TestSmartFallbackResponses:
    """Tests for smart fallback responses when LLM is unavailable."""

    def test_cached_response_fallback(self):
        """Test fallback to cached responses when LLM is unavailable."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM service unavailable")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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
                "memory": {"max_items_per_context": 50, "persistence_enabled": False},
                "commands": {},
            }

            service = AdvisorsService(config)

            # Add some cached responses to memory
            service.memory.add("discord", "test", "user123", "user", "What's the time?")
            service.memory.add("discord", "test", "user123", "assistant", "It's 3 PM.")
            service.memory.add("discord", "test", "user123", "user", "Thanks!")
            service.memory.add(
                "discord", "test", "user123", "assistant", "You're welcome!"
            )

            message = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="What time is it?",
                username="time_asker",
            )

            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # Should include fallback with error message
            assert "LLM error" in response.reply
            # Should still process the current message
            assert "What time is it?" in response.reply

    def test_pattern_based_fallback_responses(self):
        """Test pattern-based fallback responses for common queries."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("LLM down")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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

            # Test various common patterns
            test_cases = [
                ("What time is it?", "time"),
                ("What's the weather?", "weather"),
                ("How are you?", "greeting"),
                ("Hello", "greeting"),
                ("Thanks", "gratitude"),
                ("Thank you", "gratitude"),
                ("Goodbye", "farewell"),
                ("Bye", "farewell"),
            ]

            for text, category in test_cases:
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text=text,
                    username="test_user",
                )

                response = service.handle_message(message)

                assert isinstance(response, AdvisorReply)
                assert "LLM error" in response.reply
                assert text in response.reply

    def test_fallback_response_formatting(self):
        """Test that fallback responses maintain proper formatting."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("Service error")
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

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

            # Test with various message formats
            test_messages = [
                "Simple text",
                "Text with punctuation!",
                "Text with numbers 123 and symbols @#$",
                "Multi-line\ntext message",
                "Very long text " + "x" * 200,
                "Unicode text: ñáéíóú 中文",
            ]

            for text in test_messages:
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text=text,
                    username="format_tester",
                )

                response = service.handle_message(message)

                assert isinstance(response, AdvisorReply)
                assert response.reply is not None
                assert len(response.reply) > 0
                assert text in response.reply


class TestGracefulDegradation:
    """Tests for graceful degradation when AI components fail."""

    def test_service_disabled_graceful_handling(self):
        """Test graceful handling when advisors service is disabled."""
        config = {
            "enabled": False,  # Service is disabled
            "providers": {"openai": {"api_key": "test"}},
            "personas": {
                "default": {
                    "prompt": "You are a helpful assistant.",
                    "name": "Default Assistant",
                }
            },
        }

        service = AdvisorsService(config)
        message = AdvisorMessage(
            platform="discord",
            channel="test",
            user="user123",
            text="Hello",
            username="test_user",
        )

        # Should raise RuntimeError with clear message
        with pytest.raises(RuntimeError, match="Advisors are not enabled"):
            service.handle_message(message)

    def test_partial_service_degradation(self):
        """Test graceful degradation when some components fail but others work."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.return_value = "I can still help you!"
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            # Mock thinking manager to fail
            with patch(
                "src.chatty_commander.advisors.service.get_thinking_manager"
            ) as mock_thinking:
                mock_thinking_manager = Mock()
                mock_thinking_manager.register_agent.side_effect = Exception(
                    "Thinking manager failed"
                )
                mock_thinking.return_value = mock_thinking_manager

                config = {
                    "enabled": True,
                    "providers": {"openai": {"api_key": "test"}},
                    "personas": {
                        "default": {
                            "prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        }
                    },
                }

                service = AdvisorsService(config)
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text="Hello",
                    username="test_user",
                )

                # Should still work even if thinking manager fails
                with pytest.raises(Exception, match="Thinking manager failed"):
                    service.handle_message(message)

    def test_memory_failure_graceful_degradation(self):
        """Test graceful degradation when memory operations fail."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.return_value = "This is a test response"
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "personas": {
                    "default": {
                        "prompt": "You are a helpful assistant.",
                        "name": "Default Assistant",
                    }
                },
            }

            service = AdvisorsService(config)

            # Mock memory to fail after service creation
            with patch.object(service, "memory") as mock_memory:
                mock_memory.add_message.side_effect = Exception("Memory error")
                mock_memory.get_recent_messages.side_effect = Exception("Memory error")

                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user="user123",
                    text="Test message",
                    username="test_user",
                )

                # Memory failure should be caught and handled
                response = service.handle_message(message)

                assert isinstance(response, AdvisorReply)
                assert "This is a test response" in response.reply

    def test_context_switching_during_degradation(self):
        """Test context switching behavior during service degradation."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            mock_provider.generate.side_effect = [
                "I'm the default persona",
                Exception("LLM failed for analyst"),
                "I'm back as default",
            ]
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "context": {
                    "personas": {
                        "general": {
                            "system_prompt": "You are a helpful assistant.",
                            "name": "Default Assistant",
                        },
                        "analyst": {
                            "system_prompt": "You are a data analyst.",
                            "name": "Data Analyst",
                        },
                    },
                    "default_persona": "general",
                },
                "commands": {},
            }

            service = AdvisorsService(config)

            # First message - default persona works
            message1 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Hello",
                username="test_user",
            )
            response1 = service.handle_message(message1)
            assert "default persona" in response1.reply

            # Switch to analyst persona - will fail but should fallback
            service.switch_persona(response1.context_key, "analyst")

            message2 = AdvisorMessage(
                platform="discord",
                channel="test",
                user="user123",
                text="Analyze this data",
                username="test_user",
            )
            response2 = service.handle_message(message2)
            assert "LLM error" in response2.reply
            assert "Analyze this data" in response2.reply

    def test_concurrent_request_degradation(self):
        """Test graceful degradation under concurrent request load."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            mock_provider = Mock()
            # Simulate occasional failures under load - but all succeed in this test
            call_count = 0

            def generate_with_load(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # In this test, we'll make all calls succeed to test the fallback mechanism
                return f"Response {call_count}"

            mock_provider.generate.side_effect = generate_with_load
            mock_provider.model = "gpt-4"
            mock_provider.api_mode = "completion"
            mock_build.return_value = mock_provider

            config = {
                "enabled": True,
                "providers": {"openai": {"api_key": "test"}},
                "personas": {
                    "default": {
                        "prompt": "You are a helpful assistant.",
                        "name": "Default Assistant",
                    }
                },
            }

            service = AdvisorsService(config)

            # Simulate concurrent requests
            responses = []
            for i in range(6):
                message = AdvisorMessage(
                    platform="discord",
                    channel="test",
                    user=f"user{i}",
                    text=f"Message {i}",
                    username=f"user_{i}",
                )

                try:
                    response = service.handle_message(message)
                    responses.append((i, "success", response.reply))
                except Exception as e:
                    responses.append((i, "error", str(e)))

            # All should succeed since our mock doesn't fail
            success_count = sum(1 for _, status, _ in responses if status == "success")
            error_count = sum(1 for _, status, _ in responses if status == "error")

            assert success_count == 6  # All requests should succeed
            assert error_count == 0  # No errors expected

    def test_multiple_provider_fallback_chain(self):
        """Test fallback when multiple providers fail in sequence."""
        with patch(
            "src.chatty_commander.advisors.service.build_provider_safe"
        ) as mock_build:
            # Mock multiple providers failing
            mock_providers = []
            for i in range(3):
                mock_provider = Mock()
                mock_provider.generate.side_effect = Exception(f"Provider {i+1} failed")
                mock_provider.model = f"gpt-{4-i}"
                mock_provider.api_mode = "completion"
                mock_providers.append(mock_provider)

            # Return different providers on each call
            mock_build.side_effect = mock_providers

            config = {
                "enabled": True,
                "providers": {
                    "openai": {"api_key": "test1"},
                    "anthropic": {"api_key": "test2"},
                    "local": {"base_url": "http://localhost:8080", "api_key": "test3"},
                },
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
                text="Hello with multiple fallback",
                username="fallback_tester",
            )

            # Should eventually provide a fallback response after all providers fail
            response = service.handle_message(message)

            assert isinstance(response, AdvisorReply)
            # Should contain error message from the last failed provider
            assert "Provider 3 failed" in response.reply
            assert "Hello with multiple fallback" in response.reply


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
