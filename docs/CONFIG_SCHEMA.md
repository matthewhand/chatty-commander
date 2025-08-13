# Configuration Schema

ChattyCommander now ships with a **typed configuration** defined in Python using dataclasses.
The schema is loaded from `config.json` (or environment overrides) and validated on start up.
Each field below lists its type and purpose.

## Top‑level structure

| Field               | Type                            | Description                                |
| ------------------- | ------------------------------- | ------------------------------------------ |
| `keybindings`       | `dict[str, str]`                | Named keyboard shortcuts used by commands. |
| `commands`          | `dict[str, Command]`            | Mapping of command names to actions.       |
| `command_sequences` | `dict[str, list[SequenceStep]]` | Ordered multi‑step commands.               |
| `api_endpoints`     | `dict[str, str]`                | Base URLs used in URL actions.             |
| `state_models`      | `dict[str, list[str]]`          | Commands/models active for each state.     |
| `model_paths`       | `ModelPaths`                    | Directory locations for model files.       |
| `audio_settings`    | `AudioSettings`                 | Recording configuration.                   |
| `general_settings`  | `GeneralSettings`               | Application flags and defaults.            |

### Command

```python
@dataclass
class Command:
    action: Literal["keypress", "url", "shell", "custom_message"]
    keys: str | None = None
    url: str | None = None
    shell: str | None = None
    message: str | None = None
```

### ModelPaths

```python
@dataclass
class ModelPaths:
    idle: str
    computer: str
    chatty: str
```

### AudioSettings

```python
@dataclass
class AudioSettings:
    mic_chunk_size: int = 1024
    sample_rate: int = 16000
    audio_format: str = "int16"
```

### GeneralSettings

```python
@dataclass
class GeneralSettings:
    debug_mode: bool = False
    default_state: str = "idle"
    inference_framework: Literal["onnx", "pytorch"] = "onnx"
    start_on_boot: bool = False
    check_for_updates: bool = True
```

## Adding a custom command

1. Define a keybinding:
   ```json
   {
     "keybindings": {
       "mute": "ctrl+m"
     }
   }
   ```
2. Reference it in `commands`:
   ```json
   {
     "commands": {
       "mute_audio": { "action": "keypress", "keys": "mute" }
     }
   }
   ```
3. Add the command name to a state's `state_models` list so the model is loaded when active.

This typed schema ensures configuration errors are caught early and provides IDE type hints for contributors.
