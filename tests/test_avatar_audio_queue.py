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
        await queue.enqueue('a', 'first', b'aa')
        await queue.enqueue('a', 'second', b'bb')
        await queue.queue.join()

    asyncio.run(run())
    starts = [e['data']['message'] for e in mgr.events if e['type'] == 'avatar_audio_start']
    assert starts == ['first', 'second']


def test_interrupt_replaces_current_playback():
    mgr = StubManager()
    queue = AvatarAudioQueue(mgr)

    async def fake_play(audio):
        await asyncio.sleep(0.05)

    queue._play_audio = fake_play  # type: ignore[attr-defined]

    async def run():
        await queue.enqueue('a', 'first', b'aa')
        await asyncio.sleep(0.01)
        await queue.interrupt('a', 'priority', b'bb')
        await queue.queue.join()

    asyncio.run(run())
    starts = [e['data']['message'] for e in mgr.events if e['type'] == 'avatar_audio_start']
    assert starts[0] == 'first'
    assert starts[1] == 'priority'
    # Ensure an interrupted flag was broadcast
    assert any(
        e['data'].get('interrupted')
        for e in mgr.events
        if e['type'] == 'avatar_audio_end' and e['data']['agent_id'] == 'a'
    )
