#!/usr/bin/env python3
"""
Voice integration demo script for ChattyCommander.

Demonstrates the complete voice pipeline:
1. Wake word detection
2. Voice transcription
3. Command matching and execution
4. Status reporting

Usage:
    python scripts/voice_demo.py [--mock] [--duration 30]
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chatty_commander.app.command_executor import CommandExecutor
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.app.state_manager import StateManager
from chatty_commander.voice import VoicePipeline


def main():
    parser = argparse.ArgumentParser(description="ChattyCommander Voice Integration Demo")
    parser.add_argument(
        "--mock", action="store_true", help="Use mock components (no audio hardware)"
    )
    parser.add_argument("--duration", type=int, default=30, help="Demo duration in seconds")
    parser.add_argument("--config", default="config.json", help="Config file path")
    args = parser.parse_args()

    print("🎤 ChattyCommander Voice Integration Demo")
    print("=" * 50)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = Config(args.config)

        # Show available commands
        if config.model_actions:
            print(f"📋 Available commands ({len(config.model_actions)}):")
            for cmd_name, action in config.model_actions.items():
                action_type = list(action.keys())[0] if action else "unknown"
                print(f"   - {cmd_name} ({action_type})")
        else:
            print("⚠️  No model actions configured")
            # Add some demo commands
            config.model_actions = {
                "hello": {"keypress": {"keys": "ctrl+h"}},
                "lights": {"url": {"url": "http://example.com/lights"}},
                "music": {"message": {"text": "Playing music..."}},
            }
            print("📋 Using demo commands: hello, lights, music")

        # Create managers
        print("🔧 Initializing managers...")
        state_manager = StateManager()
        model_manager = ModelManager(config)
        command_executor = CommandExecutor(config, model_manager, state_manager)

        # Create voice pipeline
        print(f"🎤 Creating voice pipeline (mock={args.mock})...")
        pipeline = VoicePipeline(
            config_manager=config,
            command_executor=command_executor,
            state_manager=state_manager,
            use_mock=args.mock,
            wake_words=["hey_jarvis", "alexa"],
            transcription_backend="mock" if args.mock else "whisper_local",
        )

        # Show pipeline status
        status = pipeline.get_status()
        print("📊 Pipeline Status:")
        print(f"   Transcriber: {status['transcriber_info']['backend_type']}")
        print(f"   Available: {status['transcriber_available']}")
        print(f"   Wake words: {status['available_wake_words']}")

        # Add callback to show results
        commands_executed = []

        def command_callback(command_name: str, transcription: str):
            timestamp = time.strftime("%H:%M:%S")
            if command_name:
                print(f"[{timestamp}] ✅ Executed: '{command_name}' (from: '{transcription}')")
                commands_executed.append((command_name, transcription))
            else:
                print(f"[{timestamp}] ❓ No match: '{transcription}'")

        pipeline.add_command_callback(command_callback)

        # Start pipeline
        print(f"\n🔊 Starting voice pipeline for {args.duration} seconds...")
        pipeline.start()

        if args.mock:
            print("\n💡 Mock Mode Demo:")
            print("   - Simulating wake word detection and voice commands")
            print("   - No audio hardware required")

            # Demo sequence
            demo_commands = [
                ("hey_jarvis", "hello world"),
                ("alexa", "turn on the lights"),
                ("hey_jarvis", "play some music"),
                ("alexa", "unknown command"),
            ]

            for i, (wake_word, command) in enumerate(demo_commands):
                time.sleep(3)
                print(f"\n🧪 Demo {i+1}/{len(demo_commands)}: Wake word '{wake_word}'")
                pipeline.trigger_mock_wake_word(wake_word)
                time.sleep(1)
                print(f"🧪 Processing command: '{command}'")
                pipeline.process_text_command(command)

        else:
            print("\n🎯 Real Voice Mode:")
            print("   1. Say a wake word: 'Hey Jarvis' or 'Alexa'")
            print("   2. Wait for the beep/indication")
            print("   3. Say your command clearly")
            print("   4. Examples:")
            print("      - 'Hey Jarvis, hello'")
            print("      - 'Alexa, turn on the lights'")
            print("      - 'Hey Jarvis, play music'")

            # Wait for the specified duration
            for remaining in range(args.duration, 0, -5):
                print(f"⏱️  {remaining} seconds remaining...")
                time.sleep(5)

        # Stop pipeline
        print("\n🛑 Stopping voice pipeline...")
        pipeline.stop()

        # Show summary
        print("\n📊 Demo Summary:")
        print(f"   Commands executed: {len(commands_executed)}")
        for cmd_name, transcription in commands_executed:
            print(f"   - {cmd_name}: '{transcription}'")

        print("\n✅ Voice integration demo completed!")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
