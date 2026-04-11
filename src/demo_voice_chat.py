#!/usr/bin/env python3
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

"""
Voice Chat Demo with GPT-OSS:20B

This script demonstrates the complete voice chat integration:
- Ollama with GPT-OSS:20B for LLM responses
- Whisper for speech-to-text
- pyttsx3 for text-to-speech
- 3D avatar with state management

Usage:
    python demo_voice_chat.py
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.state_manager import StateManager
from chatty_commander.avatars.thinking_state import ThinkingState, ThinkingStateManager
from chatty_commander.llm.manager import LLMManager
from chatty_commander.voice.pipeline import VoicePipeline


def main():
    """Run the voice chat demo."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("🎤 Starting Voice Chat Demo with GPT-OSS:20B")
    logger.info("=" * 50)

    try:
        # Step 1: Initialize configuration
        logger.info("📋 Loading configuration...")
        config = Config()
        logger.info("✅ Configuration loaded")

        # Step 2: Initialize LLM manager with Ollama
        logger.info("🤖 Setting up LLM manager with Ollama...")
        llm_manager = LLMManager(
            preferred_backend="ollama",
            ollama_model="gpt-oss:20b",
            ollama_host="localhost:11434",
        )

        # Check if Ollama is available
        if not llm_manager.is_available():
            logger.error("❌ Ollama backend not available!")
            logger.info("💡 To fix this:")
            logger.info(
                "   1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
            )
            logger.info("   2. Pull the model: ollama pull gpt-oss:20b")
            logger.info("   3. Start Ollama: ollama serve")
            return 1

        logger.info(f"✅ LLM backend ready: {llm_manager.get_active_backend_name()}")

        # Step 3: Initialize voice pipeline
        logger.info("🎙️ Setting up voice pipeline...")
        voice_pipeline = VoicePipeline(
            transcription_backend="whisper_local", tts_backend="pyttsx3", use_mock=False
        )

        # Check voice components
        if not voice_pipeline.transcriber.is_available():
            logger.warning("⚠️  Voice transcription not available")
            logger.info("💡 Install whisper: pip install openai-whisper")
        else:
            logger.info("✅ Voice transcription ready")

        if not voice_pipeline.tts.is_available():
            logger.warning("⚠️  TTS not available")
            logger.info("💡 Install pyttsx3: pip install pyttsx3")
        else:
            logger.info("✅ Text-to-speech ready")

        # Step 4: Initialize state management
        logger.info("👤 Setting up avatar state management...")
        state_manager = StateManager()
        thinking_state_manager = ThinkingStateManager()
        logger.info("✅ Avatar state management ready")

        # Step 5: Initialize command executor
        logger.info("⚙️  Setting up command executor...")
        command_executor = CommandExecutor(config, llm_manager, state_manager)

        # Attach components to config for voice chat action
        config.llm_manager = llm_manager  # type: ignore[attr-defined]
        config.voice_pipeline = voice_pipeline  # type: ignore[attr-defined]
        command_executor.state_manager = state_manager
        logger.info("✅ Command executor ready")

        # Step 6: Demo voice chat session
        logger.info("🎬 Starting voice chat demo...")
        logger.info("💬 Say something when prompted...")

        # Set initial state
        thinking_state_manager.set_agent_state(
            "demo_agent", ThinkingState.IDLE, "Voice chat demo ready"
        )

        # Demo a few voice chat sessions
        for i in range(3):
            logger.info(f"\n🔄 Demo session {i + 1}/3")
            logger.info("🎤 Listening for voice input...")

            # Update avatar state to listening
            thinking_state_manager.set_agent_state(
                "demo_agent", ThinkingState.LISTENING, "Listening for voice input"
            )

            # Execute voice chat
            success = command_executor.execute_command("voice_chat")

            if success:
                logger.info("✅ Voice chat session completed successfully")
            else:
                logger.warning("⚠️  Voice chat session failed")

            # Small delay between sessions
            import time

            time.sleep(2)

        # Final state
        thinking_state_manager.set_agent_state(
            "demo_agent", ThinkingState.IDLE, "Voice chat demo completed"
        )
        logger.info("\n🎉 Voice chat demo completed successfully!")
        logger.info("🚀 You can now use: chatty-commander voice-chat")

        return 0

    except KeyboardInterrupt:
        logger.info("\n⏹️  Demo stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
