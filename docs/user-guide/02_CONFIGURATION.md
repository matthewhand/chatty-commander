# Configuration Guide

ChattyCommander is highly configurable through two main files: `config.json` and `.env`.

## Setting up API Keys (.env)

Start by copying `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your OpenAI or compatible LLM credentials here.

## Application Settings (config.json)

The `config.json` file handles application behavior.
You can view sample configurations in `config/`:
- `developer-tools-example.json`
- `full-assistant-example.json`
- `voice-only-example.json`

Once running, you can modify configuration in real-time using the **Web Dashboard Component**.
