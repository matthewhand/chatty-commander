#!/usr/bin/env python3
"""
Simple voice demo for video recording.
Shows the complete voice-to-code workflow step by step.
"""
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("🎤 ChattyCommander: Voice-Controlled Coding Demo")
    print("=" * 55)
    print()
    
    # Demo setup
    print("📋 Demo Setup:")
    print("   • Configuration: Voice-only mode (no GUI/web UI)")
    print("   • Transcription: Local Whisper (offline)")
    print("   • Integration: Codex-cli for code generation")
    print("   • Keybindings: Ctrl+Shift+V (start), Ctrl+Shift+Enter (paste)")
    print()
    
    # Demo workflow
    workflows = [
        {
            "input": "Hey coder, create a Python function that validates email addresses",
            "output": '''def validate_email(email: str) -> bool:
    """Validate email address format using regex."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None'''
        },
        {
            "input": "Create a function to calculate fibonacci numbers",
            "output": '''def fibonacci(n: int) -> int:
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
        },
        {
            "input": "Write a function to sort a list of dictionaries by a key",
            "output": '''def sort_dict_list(dict_list: list, key: str, reverse: bool = False) -> list:
    """Sort list of dictionaries by specified key."""
    return sorted(dict_list, key=lambda x: x.get(key, 0), reverse=reverse)'''
        }
    ]
    
    print("🎬 Recording Demo Workflow:")
    print()
    
    for i, workflow in enumerate(workflows, 1):
        print(f"📹 Scene {i}: Voice Command → Code Generation")
        print("-" * 45)
        
        # Step 1: Voice input
        print("🎤 Voice Input:")
        print(f'   "{workflow["input"]}"')
        print()
        
        # Simulate processing
        print("🔄 Processing:")
        print("   • Wake word detected: 'Hey coder'")
        time.sleep(0.5)
        print("   • Recording voice... 🔴")
        time.sleep(0.5)
        print("   • Transcribing with Whisper... 🧠")
        time.sleep(0.5)
        print("   • Sending to codex-cli... 🚀")
        time.sleep(0.5)
        
        # Step 2: Code output
        print("🤖 Generated Code:")
        print("```python")
        print(workflow["output"])
        print("```")
        print()
        
        # Step 3: Automation
        print("⌨️  Automated Actions:")
        print("   • Code automatically pasted to editor")
        print("   • Cursor positioned for immediate use")
        print("   • Ready for next voice command")
        print()
        
        if i < len(workflows):
            print("⏸️  [Pause for next scene]")
            print()
    
    # Demo benefits
    print("✨ Key Benefits Demonstrated:")
    print("   ✅ Hands-free coding - describe what you want")
    print("   ✅ Instant results - no typing or searching")
    print("   ✅ Editor agnostic - works with any text editor")
    print("   ✅ Offline capable - local processing, no internet")
    print("   ✅ No UI interruption - pure workflow integration")
    print()
    
    # Technical details
    print("🔧 Technical Implementation:")
    print("   • Wake word: OpenWakeWord (local detection)")
    print("   • Transcription: Whisper (local AI model)")
    print("   • Code generation: Codex-cli integration")
    print("   • Automation: System keybindings")
    print()
    
    print("🎯 Perfect for:")
    print("   • Rapid prototyping")
    print("   • Learning new patterns")
    print("   • Accessibility needs")
    print("   • Productive coding workflows")
    print()
    
    print("📦 Easy Setup:")
    print("   1. pip install chatty-commander[voice]")
    print("   2. Copy voice-only configuration")
    print("   3. Start voice mode: chatty voice test")
    print("   4. Begin coding with voice!")


if __name__ == "__main__":
    main()