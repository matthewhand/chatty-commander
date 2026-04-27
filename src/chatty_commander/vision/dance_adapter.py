"""
Dance Input Adapter for Chatty Commander Orchestrator.

Integrates interpretive dance mode as an expressive input method.
"""

import logging
from typing import Optional, Dict, Any, Callable

from .body_controller import BodyController
from .dance_interpreter import DanceInterpreter, FlowState, EnergyLevel

logger = logging.getLogger(__name__)


class DanceInputAdapter:
    """
    Input adapter using interpretive dance for expressive control.
    
    Unlike the gesture adapter (discrete commands), this provides
    continuous, emotional, and flow-based control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.mode = self.config.get('mode', 'interpretive')  # or 'gestural'
        
        # Initialize components
        self.body_controller = BodyController({
            'camera_index': self.config.get('camera_index', 0),
            'min_detection_confidence': self.config.get('min_detection_confidence', 0.5),
        })
        
        self.dance_interpreter = DanceInterpreter({
            'min_phrase_duration': self.config.get('min_phrase_duration', 2.0),
            'show_ghost_trail': self.config.get('show_ghost_trail', True),
        })
        
        # Callbacks
        self.command_callback: Optional[Callable[[str], None]] = None
        self.flow_callback: Optional[Callable[[FlowState], None]] = None
        
        # State
        self._is_started = False
        self.current_flow: Optional[FlowState] = None
        
    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for command execution."""
        self.command_callback = callback
    
    def set_flow_callback(self, callback: Callable[[FlowState], None]) -> None:
        """Set callback for flow state updates (for UI)."""
        self.flow_callback = callback
    
    def start(self) -> bool:
        """Start dance input adapter."""
        if not self.enabled:
            logger.info("Dance adapter disabled")
            return False
        
        if self._is_started:
            return True
        
        # Set up dance interpreter callbacks
        self.dance_interpreter.set_callbacks(
            on_command=self._on_dance_command,
            on_beat=self._on_beat,
            on_phrase=self._on_phrase
        )
        
        # Start body controller
        if not self.body_controller.start(self.config.get('camera_index', 0)):
            logger.error("Failed to start dance adapter")
            return False
        
        self._is_started = True
        logger.info(f"Dance adapter started in {self.mode} mode")
        return True
    
    def stop(self) -> None:
        """Stop dance adapter."""
        if self._is_started:
            self.body_controller.stop()
            self._is_started = False
            logger.info("Dance adapter stopped")
    
    def _on_dance_command(self, command: str, flow_state: FlowState) -> None:
        """Handle command from dance interpreter."""
        self.current_flow = flow_state
        
        logger.info(f"Dance command: {command} ({flow_state.energy.name}, {flow_state.style.value})")
        
        if self.command_callback:
            self.command_callback(command)
        
        if self.flow_callback:
            self.flow_callback(flow_state)
    
    def _on_beat(self, strength: float) -> None:
        """Handle detected beat."""
        logger.debug(f"Beat detected: {strength:.2f}")
    
    def _on_phrase(self, phrase) -> None:
        """Handle completed phrase."""
        logger.info(f"Phrase complete: {phrase.dominant_style.value}")
    
    def process_frame(self) -> Dict[str, Any]:
        """Process single frame (call in loop)."""
        if not self._is_started:
            return {}
        
        # Get frame from body controller
        ret, frame = self.body_controller._capture.read()
        if not ret:
            return {}
        
        # Detect pose
        annotated_frame, landmarks = self.body_controller.detector.detect(frame)
        
        if landmarks:
            # Process through dance interpreter
            result = self.dance_interpreter.process_frame(landmarks)
            
            # Add visualization
            if self.config.get('show_visualization', True):
                annotated_frame = self.dance_interpreter.draw_dance_overlay(
                    annotated_frame, landmarks
                )
            
            return {
                'frame': annotated_frame,
                'commands': result.get('commands', []),
                'flow_state': result.get('flow_state'),
                'on_beat': result.get('on_beat', False),
                'tempo': result.get('tempo', 0)
            }
        
        return {'frame': annotated_frame}
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            'enabled': self.enabled,
            'is_running': self._is_started,
            'mode': self.mode,
            'current_flow': {
                'energy': self.current_flow.energy.name if self.current_flow else None,
                'style': self.current_flow.style.value if self.current_flow else None,
            } if self.current_flow else None,
            **self.body_controller.get_status()
        }


def create_dance_adapter(config: Optional[Dict] = None) -> DanceInputAdapter:
    """Factory function for dance adapter."""
    return DanceInputAdapter(config)


# Example/demo
if __name__ == "__main__":
    print("Dance Input Adapter Demo")
    print("=" * 50)
    
    adapter = create_dance_adapter({
        'mode': 'interpretive',
        'show_visualization': True
    })
    
    def on_command(cmd):
        print(f"\n🎭 COMMAND: {cmd.upper()}")
    
    def on_flow(flow):
        print(f"   Energy: {flow.energy.name:12} | Style: {flow.style.value:12} | "
              f"Expansion: {flow.expansion:.2f}")
    
    adapter.set_command_callback(on_command)
    adapter.set_flow_callback(on_flow)
    
    if adapter.start():
        print("\nDance adapter started!")
        print("Dance expressively - watch the commands flow...")
        print("Press Ctrl+C to stop\n")
        
        try:
            import time
            while True:
                result = adapter.process_frame()
                if result.get('frame') is not None:
                    # Would display frame here
                    pass
                time.sleep(0.033)  # ~30fps
        except KeyboardInterrupt:
            pass
        finally:
            adapter.stop()
            print("\nStopped.")
    else:
        print("Failed to start dance adapter")
