#!/usr/bin/env python3
"""
CLI Tool for Training Body Gestures for Chatty Commander.

Interactive command-line interface for recording and mapping
custom body gestures to commands.
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chatty_commander.vision.gesture_adapter import (
    GestureInputAdapter, 
    GestureCommandMapper,
    create_gesture_adapter
)


def print_header(text: str) -> None:
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"ℹ️  {text}")


def interactive_training(adapter: GestureInputAdapter) -> None:
    """Interactive gesture training session."""
    print_header("GESTURE TRAINING MODE")
    
    print("This will guide you through training body gestures.")
    print("You'll perform each gesture for 2 seconds while the camera records.")
    print("\nPress Enter to start...")
    input()
    
    # Show default gestures
    mapper = GestureCommandMapper(adapter)
    guide = mapper.get_gesture_guide()
    
    print("\nAvailable gestures to train:")
    for i, (name, desc) in enumerate(guide.items(), 1):
        print(f"  {i}. {name:15} - {desc}")
    
    print("\nOptions:")
    print("  - Enter number to train that gesture")
    print("  - Enter custom name to create new gesture")
    print("  - 'list' to see trained gestures")
    print("  - 'map' to map gesture to command")
    print("  - 'quit' to exit")
    
    while True:
        print("\n" + "-"*40)
        choice = input("Choice: ").strip().lower()
        
        if choice == 'quit':
            break
        elif choice == 'list':
            gestures = adapter.list_trained_gestures()
            if gestures:
                print(f"\nTrained gestures: {', '.join(gestures)}")
            else:
                print("\nNo gestures trained yet.")
        elif choice == 'map':
            gesture = input("Gesture name: ").strip()
            command = input("Command to execute: ").strip()
            adapter.map_gesture_to_command(gesture, command)
            print_success(f"Mapped '{gesture}' -> '{command}'")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(guide):
                gesture_name = list(guide.keys())[idx]
                _train_single_gesture(adapter, gesture_name)
            else:
                print_error("Invalid number")
        elif choice:
            # Custom gesture name
            _train_single_gesture(adapter, choice)


def _train_single_gesture(adapter: GestureInputAdapter, name: str) -> bool:
    """Train a single gesture with countdown."""
    print(f"\n🎬 Training gesture: '{name}'")
    print("Get ready...")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("🎥 RECORDING! Perform the gesture now...")
    
    # Progress callback
    def on_progress(progress: float, frames: int):
        pct = int(progress * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r[{bar}] {pct}% ({frames} frames)", end="", flush=True)
    
    # Train
    success = adapter.train_gesture(name, duration=2.0, progress_callback=on_progress)
    
    print()  # New line after progress
    
    if success:
        print_success(f"Gesture '{name}' trained successfully!")
        
        # Suggest mapping
        default_commands = {
            'wave_right': 'next_track',
            'wave_left': 'previous_track',
            'thumbs_up': 'volume_up',
            'thumbs_down': 'volume_down',
            'point_up': 'scroll_up',
            'point_down': 'scroll_down',
            'clap': 'play_pause',
            'stop': 'stop_all',
            'ok_sign': 'confirm',
            'cross_arms': 'mute'
        }
        
        if name in default_commands:
            cmd = default_commands[name]
            print_info(f"Suggested command: '{cmd}'")
            if input(f"Map '{name}' to '{cmd}'? (y/n): ").lower() == 'y':
                adapter.map_gesture_to_command(name, cmd)
                print_success(f"Mapped '{name}' -> '{cmd}'")
        
        return True
    else:
        print_error(f"Failed to train gesture '{name}'")
        print_info("Make sure you're visible to the camera and try again")
        return False


def quick_train(adapter: GestureInputAdapter, gesture_names: list) -> None:
    """Quick train multiple gestures in sequence."""
    print_header("QUICK TRAINING")
    print(f"Will train {len(gesture_names)} gestures in sequence.")
    print("Press Enter to start...")
    input()
    
    for name in gesture_names:
        _train_single_gesture(adapter, name)
        time.sleep(0.5)
    
    print_header("TRAINING COMPLETE")
    print(f"Trained {len(gesture_names)} gestures")
    
    # Show mappings
    mappings = adapter.get_gesture_mappings()
    if mappings:
        print("\nCurrent mappings:")
        for gesture, command in mappings.items():
            print(f"  {gesture:15} -> {command}")


def list_commands() -> None:
    """List available Chatty Commander commands."""
    print_header("AVAILABLE COMMANDS")
    
    commands = {
        'media': ['play_pause', 'next_track', 'previous_track', 'volume_up', 'volume_down', 'mute'],
        'navigation': ['scroll_up', 'scroll_down', 'page_up', 'page_down', 'home', 'end'],
        'system': ['screenshot', 'lock_screen', 'sleep', 'shutdown', 'restart'],
        'browser': ['open_browser', 'new_tab', 'close_tab', 'refresh'],
        'app': ['open_terminal', 'open_file_manager', 'open_settings'],
        'voice': ['start_listening', 'stop_listening', 'toggle_wake_word']
    }
    
    for category, cmds in commands.items():
        print(f"\n{category.upper()}:")
        for cmd in cmds:
            print(f"  - {cmd}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Train body gestures for Chatty Commander',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive training mode
  %(prog)s -t wave_right wave_left thumbs_up  # Quick train gestures
  %(prog)s -l                 # List available commands
  %(prog)s --camera 1         # Use camera index 1
        """
    )
    
    parser.add_argument(
        '-t', '--train',
        nargs='+',
        metavar='GESTURE',
        help='Train specific gesture(s)'
    )
    
    parser.add_argument(
        '-l', '--list-commands',
        action='store_true',
        help='List available commands to map'
    )
    
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera index (default: 0)'
    )
    
    parser.add_argument(
        '--setup-defaults',
        action='store_true',
        help='Set up default gesture mappings'
    )
    
    args = parser.parse_args()
    
    # List commands only
    if args.list_commands:
        list_commands()
        return
    
    print_header("CHATTY COMMANDER GESTURE TRAINER")
    
    # Create adapter
    config = {
        'enabled': True,
        'camera_index': args.camera,
        'setup_defaults': args.setup_defaults
    }
    
    print_info(f"Initializing gesture adapter (camera {args.camera})...")
    adapter = create_gesture_adapter(config)
    
    # Set up command callback (for demo purposes)
    def on_command(cmd):
        print(f"\n🎯 Would execute: {cmd}\n")
    
    adapter.set_command_callback(on_command)
    
    # Start adapter
    print_info("Starting camera...")
    if not adapter.start():
        print_error("Failed to start camera")
        print_info("Check that camera is connected and not in use")
        sys.exit(1)
    
    print_success("Camera started successfully!")
    
    try:
        if args.train:
            # Quick train mode
            quick_train(adapter, args.train)
        else:
            # Interactive mode
            interactive_training(adapter)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        print_info("Stopping gesture adapter...")
        adapter.stop()
    
    print_header("GOODBYE")
    print("Your gestures are saved and ready to use!")
    print("Start Chatty Commander with gesture control enabled.")


if __name__ == "__main__":
    main()
