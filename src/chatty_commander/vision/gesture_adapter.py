"""
Gesture Adapter for Chatty Commander Orchestrator.

Integrates body wireframe detection as an input adapter,
allowing hand and body gestures to trigger commands.
"""

import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from .body_controller import BodyController, DetectedGesture

logger = logging.getLogger(__name__)


class GestureInputAdapter:
    """
    Input adapter that uses body gestures for command input.
    
    Integrates with the orchestrator to provide gesture-based control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize gesture input adapter."""
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.camera_index = self.config.get('camera_index', 0)
        
        # Initialize body controller
        controller_config = {
            'min_detection_confidence': self.config.get('min_detection_confidence', 0.5),
            'min_tracking_confidence': self.config.get('min_tracking_confidence', 0.5),
            'gesture_config_path': self.config.get('gesture_config_path', '~/.chatty_commander/gestures.json')
        }
        
        self.body_controller = BodyController(controller_config)
        self.command_callback: Optional[Callable[[str], None]] = None
        
        # Gesture feedback
        self.on_gesture_detected: Optional[Callable[[str, float], None]] = None
        self.on_training_complete: Optional[Callable[[str], None]] = None
        
        self._is_started = False
    
    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for executing commands."""
        self.command_callback = callback
        self.body_controller.set_command_callback(callback)
    
    def start(self) -> bool:
        """Start gesture input adapter."""
        if not self.enabled:
            logger.info("Gesture adapter disabled in config")
            return False
        
        if self._is_started:
            return True
        
        # Set up detection callback
        self.body_controller.set_detection_callback(self._on_gesture_detected)
        
        # Start body controller
        if self.body_controller.start(self.camera_index):
            self._is_started = True
            logger.info(f"Gesture adapter started with camera {self.camera_index}")
            
            # Log trained gestures
            gestures = self.body_controller.list_gestures()
            if gestures:
                logger.info(f"Available gestures: {gestures}")
            
            return True
        else:
            logger.error("Failed to start gesture adapter")
            return False
    
    def stop(self) -> None:
        """Stop gesture input adapter."""
        if self._is_started:
            self.body_controller.stop()
            self._is_started = False
            logger.info("Gesture adapter stopped")
    
    def _on_gesture_detected(self, gesture: DetectedGesture) -> None:
        """Handle detected gesture."""
        logger.info(f"Gesture detected: {gesture.name} ({gesture.confidence:.2f})")
        
        if self.on_gesture_detected:
            self.on_gesture_detected(gesture.name, gesture.confidence)
    
    def train_gesture(self, name: str, duration: float = 2.0) -> bool:
        """
        Train a new gesture.
        
        Args:
            name: Name for the gesture
            duration: Recording duration in seconds
            
        Returns:
            True if training successful
        """
        if not self._is_started:
            logger.error("Cannot train: Adapter not started")
            return False
        
        logger.info(f"Starting gesture training: {name}")
        
        # Progress callback for UI feedback
        def on_progress(progress: float, frames: int):
            pct = int(progress * 100)
            logger.info(f"Training {name}: {pct}% ({frames} frames)")
        
        success = self.body_controller.train_gesture(name, duration, on_progress)
        
        if success and self.on_training_complete:
            self.on_training_complete(name)
        
        return success
    
    def map_gesture_to_command(self, gesture_name: str, command: str) -> None:
        """
        Map a gesture to a Chatty Commander command.
        
        Args:
            gesture_name: Name of trained gesture
            command: Command to execute (e.g., "open_browser", "volume_up")
        """
        self.body_controller.map_gesture(gesture_name, command)
        logger.info(f"Mapped gesture '{gesture_name}' to command '{command}'")
    
    def get_gesture_mappings(self) -> Dict[str, str]:
        """Get all gesture-to-command mappings."""
        return self.body_controller.trainer.gesture_mappings
    
    def list_trained_gestures(self) -> list:
        """List all trained gesture names."""
        return self.body_controller.list_gestures()
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            'enabled': self.enabled,
            'is_running': self._is_started,
            **self.body_controller.get_status()
        }


class GestureCommandMapper:
    """
    Pre-defined gesture to command mappings for common use cases.
    
    Provides default gestures that users can train and use immediately.
    """
    
    # Pre-defined gesture templates
    DEFAULT_GESTURES = {
        'wave_right': {
            'description': 'Wave right hand',
            'command': 'next_track',
            'landmarks': ['right_wrist', 'right_elbow']
        },
        'wave_left': {
            'description': 'Wave left hand',
            'command': 'previous_track',
            'landmarks': ['left_wrist', 'left_elbow']
        },
        'thumbs_up': {
            'description': 'Thumbs up gesture',
            'command': 'volume_up',
            'landmarks': ['right_thumb', 'right_wrist']
        },
        'thumbs_down': {
            'description': 'Thumbs down gesture',
            'command': 'volume_down',
            'landmarks': ['right_thumb', 'right_wrist']
        },
        'point_up': {
            'description': 'Point index finger up',
            'command': 'scroll_up',
            'landmarks': ['right_index', 'right_wrist']
        },
        'point_down': {
            'description': 'Point index finger down',
            'command': 'scroll_down',
            'landmarks': ['right_index', 'right_wrist']
        },
        'clap': {
            'description': 'Clap hands together',
            'command': 'play_pause',
            'landmarks': ['left_wrist', 'right_wrist']
        },
        'stop': {
            'description': 'Raise hand flat (stop sign)',
            'command': 'stop_all',
            'landmarks': ['right_wrist', 'right_elbow', 'right_shoulder']
        },
        'ok_sign': {
            'description': 'Make OK sign with thumb and index',
            'command': 'confirm',
            'landmarks': ['right_thumb', 'right_index']
        },
        'cross_arms': {
            'description': 'Cross arms over chest',
            'command': 'mute',
            'landmarks': ['left_wrist', 'right_wrist', 'left_shoulder', 'right_shoulder']
        }
    }
    
    def __init__(self, adapter: GestureInputAdapter):
        """Initialize with gesture adapter."""
        self.adapter = adapter
    
    def setup_defaults(self) -> None:
        """Set up default gesture mappings."""
        for gesture_name, config in self.DEFAULT_GESTURES.items():
            command = config['command']
            self.adapter.map_gesture_to_command(gesture_name, command)
            logger.info(f"Set up default: {gesture_name} -> {command}")
    
    def get_gesture_guide(self) -> Dict[str, str]:
        """Get user-friendly gesture descriptions."""
        return {
            name: config['description']
            for name, config in self.DEFAULT_GESTURES.items()
        }
    
    def print_gesture_guide(self) -> None:
        """Print gesture training guide."""
        print("\n" + "="*60)
        print("CHATTY COMMANDER GESTURE GUIDE")
        print("="*60)
        print("\nTrain these gestures and they'll trigger commands:\n")
        
        for name, config in self.DEFAULT_GESTURES.items():
            print(f"  {name:15} -> {config['command']}")
            print(f"    Description: {config['description']}")
            print(f"    Key points: {', '.join(config['landmarks'])}")
            print()
        
        print("="*60)
        print("To train a gesture:")
        print("  1. Call adapter.train_gesture('wave_right')")
        print("  2. Perform the gesture for 2 seconds")
        print("  3. Gesture is saved and ready to use!")
        print("="*60 + "\n")


def create_gesture_adapter(config: Optional[Dict] = None) -> GestureInputAdapter:
    """
    Factory function to create and configure gesture adapter.
    
    Args:
        config: Configuration dict with keys:
            - enabled: bool (default True)
            - camera_index: int (default 0)
            - min_detection_confidence: float (default 0.5)
            - min_tracking_confidence: float (default 0.5)
            - gesture_config_path: str (default ~/.chatty_commander/gestures.json)
            
    Returns:
        Configured GestureInputAdapter
    """
    adapter = GestureInputAdapter(config)
    
    # Set up default mappings if requested
    if config and config.get('setup_defaults', False):
        mapper = GestureCommandMapper(adapter)
        mapper.setup_defaults()
    
    return adapter


# Integration example
def example_integration():
    """Example of integrating gesture adapter with Chatty Commander."""
    from ..app.orchestrator import Orchestrator
    
    # Create orchestrator
    orchestrator = Orchestrator()
    
    # Create gesture adapter
    gesture_config = {
        'enabled': True,
        'camera_index': 0,
        'setup_defaults': True  # Use default gesture mappings
    }
    gesture_adapter = create_gesture_adapter(gesture_config)
    
    # Set up command execution
    def execute_command(command: str):
        print(f"🎯 Gesture triggered: {command}")
        # In real integration, this would call orchestrator.execute_command
        # orchestrator.execute_command(command)
    
    gesture_adapter.set_command_callback(execute_command)
    
    # Start gesture input
    if gesture_adapter.start():
        print("✅ Gesture control active!")
        print("Train gestures with: adapter.train_gesture('wave_right')")
        
        # Print guide
        mapper = GestureCommandMapper(gesture_adapter)
        mapper.print_gesture_guide()
    else:
        print("❌ Failed to start gesture control")
    
    return gesture_adapter


if __name__ == "__main__":
    # Standalone demo
    adapter = create_gesture_adapter({'setup_defaults': True})
    
    # Set up command callback
    def on_command(cmd):
        print(f"\n🎯 EXECUTING: {cmd}\n")
    
    adapter.set_command_callback(on_command)
    
    # Start
    if adapter.start():
        print("Gesture adapter started. Press Ctrl+C to stop.")
        try:
            # Keep running
            import time
            while True:
                time.sleep(1)
                status = adapter.get_status()
                print(f"Status: {status['gestures_trained']} gestures trained, "
                      f"{status['fps']:.1f} FPS")
        except KeyboardInterrupt:
            pass
        finally:
            adapter.stop()
            print("Stopped.")
    else:
        print("Failed to start gesture adapter")
