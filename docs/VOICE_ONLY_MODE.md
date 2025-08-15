Voice‑Only Mode
==============

Chatty Commander can operate without the graphical avatar interface.  In this
mode responses are spoken using the built‑in text‑to‑speech (TTS) system while
the avatar UI is skipped entirely.

Enable via CLI
--------------

Run the main application with the ``--voice-only`` flag:

```
chatty-commander run --voice-only
```

Configuration
-------------

To enable voice‑only mode persistently, add the following to ``config.json``:

```json
{
  "voice_only": true
}
```

Dependencies
------------

Speech synthesis uses the optional ``pyttsx3`` package.  Install the voice
extras when desired:

```
uv add pyttsx3 --group voice
```

When the dependency is missing Chatty Commander falls back to a mock backend,
allowing tests and headless environments to run without additional
requirements.
