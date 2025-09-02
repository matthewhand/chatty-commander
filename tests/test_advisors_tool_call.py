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

from chatty_commander.advisors.service import AdvisorMessage, AdvisorsService


def test_advisors_happy_path_with_stub_provider(monkeypatch):
    # Configure advisors enabled with stub provider (no API key)
    cfg = {
        "enabled": True,
        "providers": {"model": "gpt-oss20b", "api_mode": "completion"},
        "memory": {"persistence_enabled": False},
    }

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
    assert reply.api_mode == svc.provider.api_mode

    # Follow-up: persona switch path returns bool
    assert isinstance(svc.switch_persona(reply.context_key, "default"), bool)
