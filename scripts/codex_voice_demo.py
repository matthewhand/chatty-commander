#!/usr/bin/env python3
"""
Voice-controlled codex-cli demo script.

This script demonstrates the complete workflow:
1. Voice wake word detection
2. Voice transcription 
3. Codex-cli integration
4. Code generation

Perfect for recording demo videos!
"""
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chatty_commander.voice import VoicePipeline
from chatty_commander.app.config import Config


def simulate_codex_integration(transcription: str) -> str:
    """Simulate codex-cli integration for demo purposes."""
    print(f"🔗 Sending to codex-cli: '{transcription}'")
    
    # Simulate codex-cli responses based on common requests
    responses = {
        "create a hello world function": '''def hello_world():
    """Print hello world to console."""
    print("Hello, World!")
    return "Hello, World!"''',
        
        "validate email address": '''import re

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None''',
        
        "fibonacci function": '''def fibonacci(n: int) -> int:
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
    }
    
    # Find best match
    for key, code in responses.items():
        if any(word in transcription.lower() for word in key.split()):
            return code
    
    # Default response
    return f'# Generated code for: {transcription}\nprint("Code generated successfully!")'


def demo_voice_to_code():
    """Demonstrate voice-controlled code generation."""
    print("🎤 Voice-Controlled Codex-CLI Demo")
    print("=" * 50)
    
    # Load voice-only configuration
    try:
        config = Config("config.json")
        print("✅ Loaded voice-only configuration")
    except Exception as e:
        print(f"❌ Config error: {e}")
        return
    
    # Add demo commands to config
    config.model_actions.update({
        "start_transcription": {"keypress": {"keys": "ctrl+shift+v"}},
        "end_and_paste": {"keypress": {"keys": "ctrl+shift+enter"}},
        "codex_query": {"keypress": {"keys": "ctrl+alt+c"}},
    })
    
    # Create voice pipeline with mock components
    pipeline = VoicePipeline(
        config_manager=config,
        use_mock=True,
        wake_words=["hey_coder", "start_transcription"]
    )
    
    # Demo commands to test
    demo_commands = [
        "create a hello world function",
        "create a function to validate email addresses",
        "write a fibonacci function"
    ]
    
    # Track results for demo
    results = []
    
    def demo_callback(command_name: str, transcription: str):
        """Handle voice commands and simulate codex integration."""
        timestamp = time.strftime("%H:%M:%S")
        
        if transcription:
            print(f"\n[{timestamp}] 🎤 Voice Input: '{transcription}'")
            
            # Simulate codex-cli integration
            generated_code = simulate_codex_integration(transcription)
            
            print(f"[{timestamp}] 🤖 Generated Code:")
            print("```python")
            print(generated_code)
            print("```")
            
            # Simulate pasting code (this would be automatic with real keybindings)
            print(f"[{timestamp}] ⌨️  Code pasted to editor")
            
            results.append({
                'input': transcription,
                'code': generated_code,
                'timestamp': timestamp
            })
    
    pipeline.add_command_callback(demo_callback)
    
    # Start demo
    print("\n🔊 Starting voice pipeline...")
    pipeline.start()
    
    print("\n💡 Demo Sequence:")
    print("   1. Say wake word or press Ctrl+Shift+V")
    print("   2. Speak your coding request")
    print("   3. System transcribes and sends to codex-cli") 
    print("   4. Generated code appears in editor")
    print("   5. Press Ctrl+Shift+Enter to execute")
    
    # Run demo sequence
    for i, command in enumerate(demo_commands, 1):
        print(f"\n🧪 Demo {i}/{len(demo_commands)}")
        print(f"🎯 Simulating: 'Hey coder, {command}'")
        
        # Simulate wake word detection
        time.sleep(1)
        print("🟢 Wake word detected!")
        
        # Simulate voice processing
        time.sleep(0.5)
        print("🔄 Recording voice...")
        
        # Process the command
        time.sleep(0.5)
        pipeline.process_text_command(command)
        
        # Pause between demos
        time.sleep(2)
    
    # Stop pipeline
    pipeline.stop()
    
    # Demo summary
    print(f"\n📊 Demo Complete!")
    print(f"   Commands processed: {len(results)}")
    print(f"   Total time: ~{len(demo_commands) * 4} seconds")
    
    print(f"\n🎬 Perfect for video recording!")
    print(f"   • Clear voice commands")
    print(f"   • Instant code generation")
    print(f"   • No UI interruption")
    print(f"   • Works with any editor")


if __name__ == "__main__":
    try:
        demo_voice_to_code()
    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()