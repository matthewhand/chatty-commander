# Adapter and Plugin System

ChattyCommander supports extending functionality through adapters for LLM providers, platforms, and tools.

## LLM Provider Adapters

Providers are defined in `src/chatty_commander/advisors/providers.py` and `src/chatty_commander/llm/backends.py`.

### Adding a Custom LLM Provider

1. Subclass `LLMProvider` (from `advisors/providers.py`):

```python
from chatty_commander.advisors.providers import LLMProvider

class MyCustomProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        # Call your LLM API here
        return my_api.complete(prompt, model=self.model)

    def generate_stream(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)
```

2. Register in `build_provider()` in `providers.py`:

```python
elif api_mode == "my_custom":
    return MyCustomProvider(config)
```

## Platform Adapters (Advisors Bridge)

Advisors can receive messages from multiple platforms (Discord, Slack, etc.) via the bridge system.

Configure in `config.json`:

```json
{
  "advisors": {
    "platforms": ["discord", "slack"],
    "bridge": { "token": "secret" }
  }
}
```

## Tool Adapters (MCP / Function Calling)

Tools are registered in `CompletionProvider` and `ResponsesProvider` via the `tools` config list.

### Built-in Tools

- **`browser_analyst`** — fetches and summarizes web pages

### Adding a Custom Tool

Tools follow the `openai-agents` SDK pattern:

```python
from agents import function_tool

@function_tool
def my_tool(query: str) -> str:
    """Describe what this tool does."""
    return do_something(query)
```

Register it in `providers.py` within `CompletionProvider.__init__`:

```python
tools.append(my_tool)
```

## Wake Word Model Adapters

ONNX models are loaded from state directories (`models-idle/`, `models-computer/`, `models-chatty/`). Drop in any ONNX-compatible model file — see [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) for directory layout.
