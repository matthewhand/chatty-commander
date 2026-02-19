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

from unittest.mock import MagicMock, patch

import pytest

from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService


@pytest.fixture
def mock_llm_manager():
    with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get:
        mock_manager = MagicMock()
        mock_get.return_value = mock_manager
        yield mock_manager

def test_advisors_service_uses_llm_manager(mock_llm_manager):
    """Test that AdvisorsService delegates to LLMManager."""
    config = {
        "enabled": True,
        "openai_api_key": "test-key",
        "provider": {"model": "test-model"}
    }

    # Setup mock manager response
    mock_llm_manager.generate_response.return_value = "Generated response from LLMManager"
    mock_llm_manager.active_backend.model = "test-backend-model"
    mock_llm_manager.get_active_backend_name.return_value = "mock-backend"

    service = AdvisorsService(config)

    # Verify manager initialization
    assert service.llm_manager is mock_llm_manager

    # Send message
    message = AdvisorMessage(
        platform="discord",
        channel="general",
        user="user1",
        text="Hello AI"
    )

    reply = service.handle_message(message)

    # Verify response content
    assert reply.reply == "Generated response from LLMManager"
    assert reply.model == "mock-backend"

    # Verify call arguments
    mock_llm_manager.generate_response.assert_called_once()
    call_args = mock_llm_manager.generate_response.call_args
    assert "Hello AI" in call_args[0][0]  # Prompt contains message
    assert call_args[1]["model"] == "test-backend-model"

def test_advisors_service_llm_manager_fallback(mock_llm_manager):
    """Test handling of LLMManager errors."""
    config = {"enabled": True}
    service = AdvisorsService(config)

    # Setup mock to raise error
    mock_llm_manager.generate_response.side_effect = RuntimeError("Generation failed")

    message = AdvisorMessage(
        platform="discord",
        channel="general",
        user="user1",
        text="Hello"
    )

    # Should not raise, but return error message
    reply = service.handle_message(message)

    assert "[LLM Error]" in reply.reply
    assert "Generation failed" in reply.reply
    assert reply.model == "error"
