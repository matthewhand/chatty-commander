"""
CLI commands for voice integration.

Provides voice-related subcommands for testing and configuration.
"""

import logging
import time

from .pipeline import VoicePipeline

logger = logging.getLogger(__name__)


def add_voice_subcommands(subparsers) -> None:
    """Add voice-related subcommands to CLI parser."""
    # Voice command group
    voice_parser = subparsers.add_parser(
        "voice",
        help="Voice integration commands",
        description="Test and configure voice features including wake word detection and transcription.",
    )
    voice_parser.set_defaults(func=lambda args: handle_voice_command(args))

    voice_subparsers = voice_parser.add_subparsers(dest="voice_command", help="Voice commands")

    # Test command
    test_parser = voice_subparsers.add_parser(
        "test",
        help="Test voice pipeline",
        description="Test voice pipeline with mock components or real hardware.",
    )
    test_parser.add_argument("--mock", action="store_true", help="Use mock components")
    test_parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    test_parser.add_argument("--wake-words", nargs="+", help="Wake words to use")

    # Status command
    voice_subparsers.add_parser(
        "status",
        help="Show voice system status",
        description="Display status of voice components and available backends.",
    )

    # Transcribe command
    transcribe_parser = voice_subparsers.add_parser(
        "transcribe",
        help="Test transcription",
        description="Test voice transcription by recording audio.",
    )
    transcribe_parser.add_argument(
        "--backend",
        default="whisper_local",
        choices=["whisper_local", "whisper_api", "mock"],
        help="Transcription backend to use",
    )
    transcribe_parser.add_argument(
        "--timeout", type=float, default=5.0, help="Recording timeout in seconds"
    )

    # Self-test commands
    selftest_parser = voice_subparsers.add_parser(
        "self-test",
        help="Run voice system self-tests and improvements",
        description="Use TTS→STT→LLM judge loop to test and improve voice recognition",
    )

    selftest_subparsers = selftest_parser.add_subparsers(
        dest="test_command", help="Self-test commands"
    )

    # Basic test
    basic_parser = selftest_subparsers.add_parser("run", help="Run basic self-test")
    basic_parser.add_argument("--openai-key", help="OpenAI API key for LLM judge")
    basic_parser.add_argument("--phrases", nargs="+", help="Custom test phrases")

    # Improvement loop
    improve_parser = selftest_subparsers.add_parser("improve", help="Run self-improvement loop")
    improve_parser.add_argument(
        "--iterations", type=int, default=3, help="Number of improvement iterations"
    )
    improve_parser.add_argument("--openai-key", help="OpenAI API key for LLM judge")


def handle_voice_command(
    args, config_manager=None, command_executor=None, state_manager=None
) -> None:
    if not hasattr(args, 'voice_command') or not args.voice_command:
        print("No voice command specified. Use --help for available commands.")
        return

    elif args.voice_command == "status":
        _handle_voice_status(args)
    elif args.voice_command == "transcribe":
        _handle_voice_transcribe(args)
    elif args.voice_command == "self-test":
        try:
            from .self_test import handle_self_test_command

            handle_self_test_command(args)
        except ImportError:
            print("❌ Self-test not available. Install with: pip install pyttsx3 openai")
    else:
        print(f"Unknown voice command: {args.voice_command}")


def _handle_voice_test(
    args, config_manager=None, command_executor=None, state_manager=None
) -> None:
    """Handle voice test command."""
    print("🎤 Starting voice pipeline test...")

    try:
        # Create pipeline
        pipeline = VoicePipeline(
            config_manager=config_manager,
            command_executor=command_executor,
            state_manager=state_manager,
            wake_words=args.wake_words,
            use_mock=args.mock,
        )

        # Add callback to show detected commands
        def command_callback(command_name: str, transcription: str):
            if command_name:
                print(f"✅ Command executed: '{command_name}' (from: '{transcription}')")
            else:
                print(f"❓ No command matched: '{transcription}'")

        pipeline.add_command_callback(command_callback)

        # Show status
        status = pipeline.get_status()
        print("📊 Pipeline status:")
        print(f"   Transcriber: {status['transcriber_info']['backend_type']}")
        print(f"   Available: {status['transcriber_available']}")
        print(f"   Wake words: {status['available_wake_words']}")

        # Start pipeline
        pipeline.start()
        print(f"🔊 Voice pipeline started (duration: {args.duration}s)")

        if args.mock:
            print("💡 Mock mode - use 'pipeline.trigger_mock_wake_word()' to test")
            print("💡 Or try: pipeline.process_text_command('hello world')")

            # Demonstrate mock functionality
            time.sleep(2)
            print("\n🧪 Testing mock wake word...")
            pipeline.trigger_mock_wake_word("hey_jarvis")

            time.sleep(2)
            print("\n🧪 Testing text command processing...")
            pipeline.process_text_command("hello there")

        else:
            print("🎯 Say a wake word followed by a command...")
            print("   Example: 'Hey Jarvis, hello world'")

        # Wait for specified duration
        time.sleep(args.duration)

        # Stop pipeline
        pipeline.stop()
        print("✅ Voice pipeline test completed")

    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        logger.error(f"Voice test error: {e}")


def _handle_voice_status(args) -> None:
    """Handle voice status command."""
    print("🔍 Voice System Status")
    print("=" * 40)

    try:
        # Check voice dependencies using importlib
        import importlib.util

        deps = [
            ("OpenWakeWord", "openwakeword"),
            ("Whisper (local)", "whisper"),
            ("OpenAI API", "openai"),
            ("PyAudio", "pyaudio"),
        ]

        for name, module in deps:
            if importlib.util.find_spec(module):
                print(f"✅ {name}: Available")
            else:
                print(f"❌ {name}: Not installed")

        # Test pipeline creation
        try:
            pipeline = VoicePipeline(use_mock=True)
            status = pipeline.get_status()

            print("\n📊 Pipeline Status:")
            print(f"   Transcriber: {status['transcriber_info']['backend_type']}")
            print(f"   Available: {status['transcriber_available']}")
            print(f"   Sample rate: {status['transcriber_info']['sample_rate']} Hz")
            print(f"   Channels: {status['transcriber_info']['channels']}")

        except Exception as e:
            print(f"❌ Pipeline test failed: {e}")

    except Exception as e:
        print(f"❌ Status check failed: {e}")


def _handle_voice_transcribe(args) -> None:
    """Handle voice transcribe command."""
    print(f"🎤 Testing transcription with {args.backend} backend...")

    try:
        from .transcription import VoiceTranscriber

        transcriber = VoiceTranscriber(backend=args.backend, record_timeout=args.timeout)

        if not transcriber.is_available():
            print(f"❌ Transcription backend '{args.backend}' not available")
            return

        print(f"📊 Backend info: {transcriber.get_backend_info()}")

        if args.backend == "mock":
            # Use mock transcription
            result = transcriber.transcribe_audio_data(b"dummy_audio")
            print(f"🧪 Mock transcription: '{result}'")
        else:
            # Record and transcribe
            print(f"🔴 Recording for {args.timeout} seconds... Speak now!")
            result = transcriber.record_and_transcribe()

            if result:
                print(f"✅ Transcription: '{result}'")
            else:
                print("❌ No transcription received")

    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        logger.error(f"Transcription test error: {e}")


# Example usage function for integration testing
def demo_voice_integration(config_manager=None, command_executor=None) -> None:
    """Demo function showing voice integration capabilities."""
    print("🎤 ChattyCommander Voice Integration Demo")
    print("=" * 50)

    try:
        # Create pipeline with mock components for demo
        pipeline = VoicePipeline(
            config_manager=config_manager, command_executor=command_executor, use_mock=True
        )

        # Show available commands
        if config_manager and hasattr(config_manager, 'model_actions'):
            print("📋 Available commands:")
            for cmd_name in config_manager.model_actions.keys():
                print(f"   - {cmd_name}")

        # Add demo callback
        def demo_callback(command_name: str, transcription: str):
            if command_name:
                print(f"🎯 Executed: {command_name} ('{transcription}')")
            else:
                print(f"❓ Unknown: '{transcription}'")

        pipeline.add_command_callback(demo_callback)

        # Start pipeline
        pipeline.start()
        print("\n🔊 Voice pipeline active!")

        # Demo some commands
        demo_commands = ["hello world", "turn on the lights", "play some music", "unknown command"]

        for cmd in demo_commands:
            print(f"\n🧪 Testing: '{cmd}'")
            pipeline.process_text_command(cmd)
            time.sleep(1)

        # Stop pipeline
        pipeline.stop()
        print("\n✅ Demo completed!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Voice demo error: {e}")
