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

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

try:
    from chatty_commander.voice.wakeword import MockWakeWordDetector, WakeWordDetector

    VOICE_AVAILABLE = True
# Handle specific exception case
except ImportError:
    MockWakeWordDetector = None  # type: ignore
    WakeWordDetector = None  # type: ignore
    VOICE_AVAILABLE = False


class CommandSink(Protocol):
    """CommandSink class.

    TODO: Add class description.
    """
    
    def execute_command(self, command_name: str) -> Any:  # pragma: no cover - protocol
        """Execute Command with (self, command_name: str).

        TODO: Add detailed description and parameters.
        """
        
        ...


class AdvisorSink(Protocol):
    """AdvisorSink class.

    TODO: Add class description.
    """
    
    def handle_message(self, message: Any) -> Any:  # pragma: no cover - protocol
        """Process with (self, message: Any).

        TODO: Add detailed description and parameters.
        """
        
        ...


class InputAdapter(Protocol):
    """InputAdapter class.

    TODO: Add class description.
    """
    
    name: str

    def start(self) -> None:  # pragma: no cover - protocol
        """Start with (self).

        TODO: Add detailed description and parameters.
        """
        
        ...

    def stop(self) -> None:  # pragma: no cover - protocol
        """Stop with (self).

        TODO: Add detailed description and parameters.
        """
        
        ...


@dataclass
class OrchestratorFlags:
    """OrchestratorFlags class.

    TODO: Add class description.
    """
    
    enable_text: bool = False
    enable_gui: bool = False
    enable_web: bool = False
    enable_openwakeword: bool = False
    enable_computer_vision: bool = False
    enable_discord_bridge: bool = False


class TextInputAdapter:
    """TextInputAdapter class.

    TODO: Add class description.
    """
    
    name = "text"

    def __init__(self, on_command: Callable[[str], None]) -> None:
        self._on_command = on_command
        self._started = False

    def start(self) -> None:
        """Start with (self).

        TODO: Add detailed description and parameters.
        """
        
        self._started = True

    def stop(self) -> None:
        """Stop with (self).

        TODO: Add detailed description and parameters.
        """
        
        self._started = False

    # Helper for tests/manual feeding
    def feed(self, text: str) -> None:
        """Feed with (self, text: str).

        TODO: Add detailed description and parameters.
        """
        
        # Apply conditional logic
        if self._started:
            self._on_command(text)


class DummyAdapter:
    """Placeholder adapters for GUI/WEB/CV/WakeWord/Discord bridge.

    Real implementations exist or will be provided elsewhere (e.g., WebMode server, Node bridge).
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._started = False

    def start(self) -> None:
        """Start with (self).

        TODO: Add detailed description and parameters.
        """
        
        self._started = True

    def stop(self) -> None:
        """Stop with (self).

        TODO: Add detailed description and parameters.
        """
        
        self._started = False


class OpenWakeWordAdapter:
    """Adapter for OpenWakeWord wake word detection."""

    name = "openwakeword"

    def __init__(
        self, on_wake_word: Callable[[str, float], None], config: Any = None
    ) -> None:
        self._on_wake_word = on_wake_word
        self._config = config
        self._detector: Any = None
        self._started = False

    def start(self) -> None:
        """Start with (self).

        TODO: Add detailed description and parameters.
        """
        
        # Apply conditional logic
        if not VOICE_AVAILABLE:
            raise ImportError("Voice dependencies not available. Install with: uv sync")

        # Apply conditional logic
        if self._started:
            return

        # Get wake word configuration from config
        wake_words = getattr(self._config, "wake_words", None) or [
            "hey_jarvis",
            "alexa",
        ]
        threshold = getattr(self._config, "wake_word_threshold", 0.5)

        # Logic flow
        # Use MockWakeWordDetector if no audio hardware available
        if WakeWordDetector is not None and MockWakeWordDetector is not None:
            try:
                self._detector = WakeWordDetector(
                    wake_words=wake_words, threshold=threshold
                )
            except Exception:
                # Fallback to mock detector
                self._detector = MockWakeWordDetector()
        else:
            self._detector = None

        # Logic flow
        # Add callback for wake word detection
        if self._detector is not None:
            self._detector.add_callback(self._handle_wake_word)
            self._detector.start_listening()
        self._started = True

    def stop(self) -> None:
        """Stop with (self).

        TODO: Add detailed description and parameters.
        """
        
        # Apply conditional logic
        if self._detector and self._started:
            self._detector.stop_listening()
        self._started = False

    def _handle_wake_word(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection by calling the callback."""
        self._on_wake_word(wake_word, confidence)


class ModeOrchestrator:
    """Unifies multiple operating modes by selecting and starting adapters.

    - Text mode: stdin-like commands or injected strings
    - GUI mode: placeholder until GUI module provides an adapter
    - Web mode: placeholder referencing existing FastAPI server lifecycle
    - OpenWakeWord: optional adapter placeholder
    - Computer Vision: optional adapter placeholder
    - Discord bridge: optional adapter placeholder for Node.js bridge
    """

    def __init__(
        self,
        *,
        config: Any,
        command_sink: CommandSink,
        advisor_sink: AdvisorSink | None = None,
        flags: OrchestratorFlags | None = None,
    ) -> None:
        self.config = config
        self.command_sink = command_sink
        self.advisor_sink = advisor_sink
        self.flags = flags or OrchestratorFlags()
        self.adapters: list[InputAdapter] = []

    def _create_text_adapter(self) -> InputAdapter | None:
        """Create text input adapter if enabled."""
        if self.flags.enable_text:
            return TextInputAdapter(on_command=self._dispatch_command)
        return None

    def _create_gui_adapter(self) -> InputAdapter | None:
        """Create GUI adapter if enabled."""
        if self.flags.enable_gui:
            return DummyAdapter("gui")
        return None

    def _create_web_adapter(self) -> InputAdapter | None:
        """Create web adapter if enabled."""
        if self.flags.enable_web:
            return DummyAdapter("web")
        return None

    def _create_openwakeword_adapter(self) -> InputAdapter | None:
        """Create OpenWakeWord adapter if enabled and available."""
        if not self.flags.enable_openwakeword:
            return None

        if VOICE_AVAILABLE:
            try:
                return OpenWakeWordAdapter(self._handle_wake_word, self.config)  # type: ignore
            except Exception:
                return DummyAdapter("openwakeword")
        else:
            return DummyAdapter("openwakeword")

    def _create_computer_vision_adapter(self) -> InputAdapter | None:
        """Create computer vision adapter if enabled."""
        if self.flags.enable_computer_vision:
            return DummyAdapter("computer_vision")
        return None

    def _create_discord_bridge_adapter(self) -> InputAdapter | None:
        """Create Discord bridge adapter if enabled and configured."""
        if not self.flags.enable_discord_bridge:
            return None

        advisors_config = getattr(self.config, "advisors", {})
        if advisors_config.get("enabled", False):
            return DummyAdapter("discord_bridge")
        return None

    def _create_gesture_adapter(self) -> InputAdapter | None:
        """Create gesture input adapter if enabled."""
        if not self.flags.enable_gesture:
            return None

        try:
            from ..vision.gesture_adapter import GestureInputAdapter
            adapter = GestureInputAdapter({
                'enabled': True,
                'camera_index': getattr(self.config, 'gesture_camera_index', 0),
                'setup_defaults': getattr(self.config, 'gesture_setup_defaults', False),
                'min_detection_confidence': getattr(self.config, 'gesture_min_confidence', 0.5),
                'min_tracking_confidence': getattr(self.config, 'gesture_min_tracking', 0.5)
            })
            # Set up command callback to route to orchestrator
            adapter.set_command_callback(self._dispatch_command)
            return adapter
        except Exception as e:
            logger.warning(f"Failed to create gesture adapter: {e}")
            return DummyAdapter("gesture")

    def select_adapters(self) -> list[str]:
        """
        Select and instantiate input adapters based on feature flags.

        Creates adapters for each enabled feature: text, GUI, web,
        voice (OpenWakeWord), computer vision, gesture, and Discord bridge.
        Handles graceful fallback to dummy adapters when initialization fails.

        Returns:
            List of selected adapter names
        """
        selected: list[InputAdapter] = []

        # Create adapters for each enabled feature
        adapters_to_try = [
            self._create_text_adapter(),
            self._create_gui_adapter(),
            self._create_web_adapter(),
            self._create_openwakeword_adapter(),
            self._create_computer_vision_adapter(),
            self._create_gesture_adapter(),
            self._create_discord_bridge_adapter(),
        ]

        # Filter out None values
        selected = [adapter for adapter in adapters_to_try if adapter is not None]

        self.adapters = selected
        return [a.name for a in selected]

    def start(self) -> list[str]:
        """Start with (self).

        TODO: Add detailed description and parameters.
        """
        
        # Apply conditional logic
        if not self.adapters:
            self.select_adapters()
        # Process each item
        for adapter in self.adapters:
            adapter.start()
        # Build filtered collection
        # Process each item
        return [a.name for a in self.adapters]

    def stop(self) -> None:
        """Stop with (self).

        TODO: Add detailed description and parameters.
        """
        
        # Process each item
        for adapter in self.adapters:
            try:
                adapter.stop()
            # Handle specific exception case
            except Exception:
                pass

    # Routing
    def _dispatch_command(self, command_name: str) -> Any:
        return self.command_sink.execute_command(command_name)

    def _handle_wake_word(self, wake_word: str, confidence: float) -> None:
        """Handle wake word detection."""
        # For now, treat wake word as a command trigger
        # In the future, this could activate voice input or advisor mode
        command_name = f"wake_word_{wake_word}"
        try:
            self._dispatch_command(command_name)
        except Exception:
            # If no specific wake word command, try a generic wake command
            try:
                self._dispatch_command("wake")
            except Exception:
                # If no wake command, log the detection
                pass  # Could add logging here if needed
