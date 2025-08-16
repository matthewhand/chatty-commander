"""
CLI commands for LLM integration.

Provides LLM-related subcommands for testing and configuration.
"""

import logging

from .manager import LLMManager
from .processor import CommandProcessor

logger = logging.getLogger(__name__)


def add_llm_subcommands(subparsers) -> None:
    """Add LLM-related subcommands to CLI parser."""

    # LLM command group
    llm_parser = subparsers.add_parser(
        "llm",
        help="LLM integration commands",
        description="Test and configure LLM features including natural language command processing.",
    )

    llm_subparsers = llm_parser.add_subparsers(dest="llm_command", help="LLM commands")

    # Status command
    llm_subparsers.add_parser(
        "status",
        help="Show LLM system status",
        description="Display status of LLM backends and availability.",
    )

    # Test command
    test_parser = llm_subparsers.add_parser(
        "test", help="Test LLM backends", description="Test LLM backends with sample prompts."
    )
    test_parser.add_argument("--backend", help="Specific backend to test")
    test_parser.add_argument("--prompt", default="Hello, how are you?", help="Test prompt")
    test_parser.add_argument("--mock", action="store_true", help="Use mock backend only")

    # Process command
    process_parser = llm_subparsers.add_parser(
        "process",
        help="Process natural language command",
        description="Test command processing with natural language input.",
    )
    process_parser.add_argument("text", help="Natural language command to process")
    process_parser.add_argument("--mock", action="store_true", help="Use mock backend only")

    # Backends command
    llm_subparsers.add_parser(
        "backends",
        help="List available backends",
        description="Show information about all LLM backends.",
    )


def handle_llm_command(args, config_manager=None) -> None:
    """Handle LLM-related CLI commands."""

    if not hasattr(args, 'llm_command') or not args.llm_command:
        print("No LLM command specified. Use --help for available commands.")
        return

    if args.llm_command == "status":
        _handle_llm_status(args)
    elif args.llm_command == "test":
        _handle_llm_test(args)
    elif args.llm_command == "process":
        _handle_llm_process(args, config_manager)
    elif args.llm_command == "backends":
        _handle_llm_backends(args)
    else:
        print(f"Unknown LLM command: {args.llm_command}")


def _handle_llm_status(args) -> None:
    """Handle LLM status command."""
    print("🧠 LLM System Status")
    print("=" * 40)

    try:
        # Check LLM dependencies
        import importlib.util

        deps = [
            ("OpenAI", "openai"),
            ("Requests (Ollama)", "requests"),
            ("Transformers (Local)", "transformers"),
            ("PyTorch (Local)", "torch"),
        ]

        print("📦 Dependencies:")
        for name, module in deps:
            if importlib.util.find_spec(module):
                print(f"   ✅ {name}: Available")
            else:
                print(f"   ❌ {name}: Not installed")

        # Test LLM manager
        print("\n🧠 LLM Manager:")
        manager = LLMManager(use_mock=True)  # Start with mock for status

        print(f"   Active backend: {manager.get_active_backend_name()}")
        print(f"   Available: {manager.is_available()}")

        # Show all backends
        all_info = manager.get_all_backends_info()
        print("\n📊 Backend Status:")
        for backend_name, info in all_info.items():
            if backend_name == "active":
                continue

            available = info.get("available", False)
            status_icon = "✅" if available else "❌"
            print(
                f"   {status_icon} {backend_name}: {'Available' if available else 'Not available'}"
            )

            if "error" in info:
                print(f"      Error: {info['error']}")

        # Environment variables
        print("\n🔧 Environment:")
        env_vars = ["OPENAI_API_KEY", "OPENAI_API_BASE", "OLLAMA_HOST", "LLM_BACKEND"]

        for var in env_vars:
            import os

            value = os.getenv(var)
            if value:
                # Mask API keys
                if "KEY" in var and len(value) > 8:
                    display_value = value[:4] + "..." + value[-4:]
                else:
                    display_value = value
                print(f"   {var}: {display_value}")
            else:
                print(f"   {var}: Not set")

    except Exception as e:
        print(f"❌ Status check failed: {e}")


def _handle_llm_test(args) -> None:
    """Handle LLM test command."""
    print("🧪 Testing LLM backends...")

    try:
        manager = LLMManager(use_mock=args.mock)

        if args.backend:
            # Test specific backend
            print(f"Testing backend: {args.backend}")
            result = manager.test_backend(args.backend, args.prompt)

            if result.get("success"):
                print("✅ Success!")
                print(f"   Response: {result['response']}")
                print(f"   Time: {result['response_time']:.3f}s")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        else:
            # Test active backend
            backend_name = manager.get_active_backend_name()
            print(f"Testing active backend: {backend_name}")

            try:
                response = manager.generate_response(args.prompt, max_tokens=50)
                print("✅ Success!")
                print(f"   Response: {response}")
            except Exception as e:
                print(f"❌ Failed: {e}")

        # Show backend info
        info = manager.get_backend_info()
        print("\n📊 Backend Info:")
        for key, value in info.items():
            print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ LLM test failed: {e}")


def _handle_llm_process(args, config_manager=None) -> None:
    """Handle LLM process command."""
    print(f"🔄 Processing command: '{args.text}'")

    try:
        # Create LLM manager and processor
        llm_manager = LLMManager(use_mock=args.mock)
        processor = CommandProcessor(llm_manager=llm_manager, config_manager=config_manager)

        # Show available commands
        status = processor.get_processor_status()
        print(f"📋 Available commands: {', '.join(status['available_commands'])}")

        # Process the command
        command, confidence, explanation = processor.process_command(args.text)

        print("\n🎯 Processing Result:")
        if command:
            print(f"   ✅ Matched command: {command}")
            print(f"   🎲 Confidence: {confidence:.2f}")
            print(f"   💭 Explanation: {explanation}")

            # Show command details
            cmd_explanation = processor.explain_command(command)
            print(f"   📝 Action: {cmd_explanation.get('description', 'Unknown')}")
        else:
            print("   ❌ No command matched")
            print(f"   💭 Reason: {explanation}")

        # Show suggestions
        suggestions = processor.get_command_suggestions(args.text[:3])
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions[:3]:
                print(f"   - {suggestion['command']} (confidence: {suggestion['confidence']:.2f})")

    except Exception as e:
        print(f"❌ Command processing failed: {e}")


def _handle_llm_backends(args) -> None:
    """Handle LLM backends command."""
    print("🧠 LLM Backends Information")
    print("=" * 40)

    try:
        manager = LLMManager(use_mock=True)  # Include mock for complete info
        all_info = manager.get_all_backends_info()

        active_backend = all_info.pop("active", "none")
        print(f"🎯 Active Backend: {active_backend}")
        print()

        for backend_name, info in all_info.items():
            available = info.get("available", False)
            status_icon = "✅" if available else "❌"

            print(f"{status_icon} {backend_name.upper()}")
            print(f"   Available: {available}")

            # Backend-specific info
            if backend_name == "openai":
                print(f"   Base URL: {info.get('base_url', 'N/A')}")
                print(f"   Has API Key: {info.get('has_api_key', False)}")
            elif backend_name == "ollama":
                print(f"   Host: {info.get('host', 'N/A')}")
                print(f"   Model: {info.get('model', 'N/A')}")
            elif backend_name == "local":
                print(f"   Model: {info.get('model_name', 'N/A')}")
                print(f"   Device: {info.get('device', 'N/A')}")
            elif backend_name == "mock":
                print(f"   Responses: {info.get('responses_count', 0)}")
                print(f"   Calls: {info.get('call_count', 0)}")

            if "error" in info:
                print(f"   ❌ Error: {info['error']}")

            print()

    except Exception as e:
        print(f"❌ Failed to get backend information: {e}")


def demo_llm_integration(config_manager=None) -> None:
    """Demo function showing LLM integration capabilities."""
    print("🧠 ChattyCommander LLM Integration Demo")
    print("=" * 50)

    try:
        # Create LLM manager and processor
        llm_manager = LLMManager(use_mock=True)
        processor = CommandProcessor(llm_manager=llm_manager, config_manager=config_manager)

        # Show status
        status = processor.get_processor_status()
        print(f"🧠 LLM Backend: {status['llm_backend']}")
        print(f"📋 Available Commands: {', '.join(status['available_commands'])}")

        # Demo natural language processing
        demo_inputs = [
            "hello there",
            "turn on the lights please",
            "I want to play some music",
            "what's the weather like?",
            "completely unknown command",
        ]

        print("\n🔄 Processing Demo Commands:")
        for user_input in demo_inputs:
            print(f"\n💬 Input: '{user_input}'")

            command, confidence, explanation = processor.process_command(user_input)

            if command:
                print(f"   ✅ → {command} (confidence: {confidence:.2f})")
                print(f"   💭 {explanation}")
            else:
                print(f"   ❌ No match ({explanation})")

        print("\n✅ LLM integration demo completed!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"LLM demo error: {e}")
