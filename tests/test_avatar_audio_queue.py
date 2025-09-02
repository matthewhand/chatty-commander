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

import asyncio

from src.chatty_commander.web.routes.avatar_ws import AvatarAudioQueue


class StubManager:
    def __init__(self):
        self.events = []

    def broadcast_state_change(self, message):
        self.events.append(message)


def test_queue_processes_sequentially():
    mgr = StubManager()
    queue = AvatarAudioQueue(mgr)

    async def run():
        await queue.enqueue("a", "first", b"aa")
        await queue.enqueue("a", "second", b"bb")
        await queue.queue.join()

    asyncio.run(run())
    starts = [
        e["data"]["message"] for e in mgr.events if e["type"] == "avatar_audio_start"
    ]
    assert starts == ["first", "second"]


def test_interrupt_replaces_current_playback():
    mgr = StubManager()
    queue = AvatarAudioQueue(mgr)

    async def fake_play(audio):
        await asyncio.sleep(0.05)

    queue._play_audio = fake_play  # type: ignore[attr-defined]

    async def run():
        await queue.enqueue("a", "first", b"aa")
        await asyncio.sleep(0.01)
        await queue.interrupt("a", "priority", b"bb")
        await queue.queue.join()

    asyncio.run(run())
    starts = [
        e["data"]["message"] for e in mgr.events if e["type"] == "avatar_audio_start"
    ]
    assert starts[0] == "first"
    assert starts[1] == "priority"
    # Ensure an interrupted flag was broadcast
    assert any(
        e["data"].get("interrupted")
        for e in mgr.events
        if e["type"] == "avatar_audio_end" and e["data"]["agent_id"] == "a"
    )
