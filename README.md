<p align="center">
  <img src="https://raw.githubusercontent.com/matthewhand/chatty-commander/main/icon.svg" alt="Chatty Commander Logo" width="150">
</p>

<h1 align="center">Chatty Commander</h1>

<p align="center">
  <strong>Your Personal, Voice-Activated AI Command Center for Desktop Control.</strong>
  <br>
  Modular, private-by-default, and endlessly extensible.
</p>

<p align="center">
  <!-- Badges -->
  <a href="https://github.com/matthewhand/chatty-commander/actions/workflows/ci.yml">
    <img src="https://github.com/matthewhand/chatty-commander/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  </a>
  <a href="https://github.com/matthewhand/chatty-commander/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </a>
  <a href="https://github.com/matthewhand/chatty-commander/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
  </a>
</p>

---

**Chatty Commander** is not just another voice assistant. It's a powerful, local-first framework for creating personalized AI agents that control your computer. With a low-resource, always-on wake word, it gives you hands-free command over your digital environment, from launching applications and running scripts to orchestrating complex, multi-step workflows.

Built on a modular, interface-driven architecture, every component—from the AI model to the user interface—is swappable. Run it as a lightweight command-line tool, or enable the optional 3D avatar for a full virtual companion experience.

## ✨ Core Features

*   **🗣️ Voice-Activated Command & Control:** Uses a low-compute, offline wake word engine (`openwakeword`) for instant, private activation.
*   **🧠 Swappable AI Brains:** Defaults to local models via **Ollama** (including `gpt-oss:20b`), with a fallback to `transformers`. Easily extendable to any OpenAI-compatible API.
*   **🎭 Dynamic Personas:** Leverage the `openai-agents` library to create distinct AI personalities, each with its own voice, avatar, and command set. Switch between a helpful assistant, a sci-fi captain, or a code-savvy developer on the fly.
*   **💻 Deep Desktop Integration:** Execute shell commands, manage files, control applications, and trigger complex workflows with natural language.
*   **🔌 Radically Extensible Plugin System:** The entire system is built on dependency injection. Add new commands, services, or even entire user interfaces as plugins without touching the core code.
*   **🎭 Optional 3D Avatar:** Enable a real-time, lip-synced 3D avatar in a transparent desktop window for a visually engaging experience. (Powered by a simple WebUI frontend).
*   **🌐 Multi-Platform Bridge:** An external Node.js bridge allows Chatty Commander to integrate with messaging platforms like Discord and Slack, acting as a centralized "brain" for your bots.
*   **🔒 Private by Default:** All core operations, including wake word and local LLM inference, run entirely offline. Cloud connections are explicit and opt-in.

## 🚀 Quickstart

Get Chatty Commander up and running in minutes.

### Prerequisites

*   Python 3.11+
*   [uv](https://github.com/astral-sh/uv) (for fast dependency management)
*   (Optional) [Ollama](https://ollama.ai/) running locally for AI commands.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/matthewhand/chatty-commander.git
    cd chatty-commander
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    uv sync
    ```

### Running Chatty Commander

Activate the environment first: `source .venv/bin/activate`

*   **Interactive Shell Mode (Default):**
    ```bash
    uv run python -m src.chatty_commander.main
    ```

*   **Web API Mode (for Frontend/Bridge):**
    ```bash
    uv run python -m src.chatty_commander.main --web --no-auth
    # API will be available at http://127.0.0.1:8000
    # OpenAPI docs at http://127.0.0.1:8000/docs
    ```

*   **GUI System Tray Mode:**
    ```bash
    uv run python -m src.chatty_commander.main --gui
    ```

*   **Execute a Single Command:**
    ```bash
    uv run python -m src.chatty_commander.main exec your_command_name
    ```

## Architecture Overview

Chatty Commander is built on a decoupled, modular architecture designed for maximum flexibility.

<p align="center">
  <em>(A diagram would go here, showing the flow from Wake Word -> Intent Parser -> DI Container -> Command Executor -> Response (TTS/Avatar/CLI))</em>
</p>

*   **Core Service (Python/FastAPI):** Manages state, orchestrates plugins, and serves the web API.
*   **Plugin System:** Uses dependency injection to register commands, wake word engines, STT/TTS providers, and more.
*   **Model Orchestrator:** Intelligently routes LLM requests to the best available provider (local Ollama, Transformers, or remote APIs).
*   **Frontend (React/WebUI):** A simple, optional frontend served by the Python backend for settings and the 3D avatar.

## 🤝 Contributing

We welcome contributions of all kinds! Whether it's a new plugin, a bug fix, or documentation improvements, we'd love to have your help. Please see our `docs/DEVELOPER_SETUP.md` to get started.

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

*   Built with [OpenWakeWord](https://github.com/dscripka/openWakeWord) for wake word detection
*   Powered by [Ollama](https://ollama.ai/) for local AI inference
*   UI built with modern web technologies for cross-platform compatibility

