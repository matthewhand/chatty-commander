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

import pytest

from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService


class DummyConfig:
    advisors = {
        "enabled": True,
        "providers": {
            "llm_api_mode": "completion",
            "model": "gpt-oss20b",
        },
        "context": {
            "personas": {
                "general": {"system_prompt": "You are helpful."},
                "discord_default": {"system_prompt": "You are a Discord bot."},
            },
            "default_persona": "general",
        },
    }


def test_advisors_service_echo_reply():
    svc = AdvisorsService(config=DummyConfig())
    msg = AdvisorMessage(platform="discord", channel="c1", user="u1", text="hello")
    reply = svc.handle_message(msg)
    assert reply is not None
    assert isinstance(reply.reply, str)
    assert reply.model == "gpt-oss20b"
    assert reply.api_mode in ("completion", "responses")


def test_advisors_service_disabled_returns_notice():
    class DisabledConfig:
        advisors = {"enabled": False}

    svc = AdvisorsService(config=DisabledConfig())
    msg = AdvisorMessage(platform="slack", channel="c2", user="u2", text="ping")
    with pytest.raises(RuntimeError) as exc:
        _ = svc.handle_message(msg)
    assert "not enabled" in str(exc.value)
