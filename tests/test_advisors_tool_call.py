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

from unittest.mock import Mock, patch

from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService


def test_advisors_happy_path_with_stub_provider(monkeypatch):
    # Configure advisors enabled with stub provider (no API key)
    cfg = {
        "enabled": True,
        "providers": {"model": "gpt-oss20b", "api_mode": "completion", "api_key": None},
        "memory": {"persistence_enabled": False},
    }

    # Mock the LLM manager to return a predictable stub response
    mock_manager = Mock()
    mock_manager.generate_response.return_value = "advisor:gpt-oss20b/completion: hello world"
    mock_manager.active_backend = Mock()
    mock_manager.active_backend.model = "gpt-oss20b"
    mock_manager.get_active_backend_name.return_value = "gpt-oss20b"

    with patch("chatty_commander.llm.manager.get_global_llm_manager") as mock_get_llm:
        mock_get_llm.return_value = mock_manager

        svc = AdvisorsService(cfg)
        msg = AdvisorMessage(
            platform="discord", channel="c1", user="u1", text="hello world"
        )
        reply = svc.handle_message(msg)

        assert (
            reply.reply.startswith("advisor:gpt-oss20b/completion")
            or "hello world" in reply.reply
        )
        assert reply.model == svc.provider.model
        # api_mode is internally converted to "chat" by the service
        assert reply.api_mode in ("completion", "chat")

        # Follow-up: persona switch path returns bool
        assert isinstance(svc.switch_persona(reply.context_key, "default"), bool)
