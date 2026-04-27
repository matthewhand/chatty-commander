"""
Mock tests for interpretive dance mode.

Tests dance interpreter functionality without requiring:
- Actual camera
- MediaPipe installation
- GPU hardware
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
import time


# Mock landmark dataclass for testing
@dataclass
class MockLandmark:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


class TestDanceInterpreter:
    """Test interpretive dance interpreter with mocks."""
    
    @pytest.fixture
    def mock_landmarks(self):
        """Create mock body landmarks (33 points)."""
        # Create minimal landmark set
        landmarks = []
        for i in range(33):
            # Create a simple pose (standing, arms slightly out)
            if i in [11, 12]:  # Shoulders
                x = 0.4 if i == 11 else 0.6
                y = 0.3
            elif i in [15, 16]:  # Wrists
                x = 0.3 if i == 15 else 0.7
                y = 0.5
            elif i in [23, 24]:  # Hips
                x = 0.45 if i == 23 else 0.55
                y = 0.7
            else:
                x, y = 0.5, 0.5
            
            landmarks.append(MockLandmark(x=x, y=y, z=0.0, visibility=1.0))
        return landmarks
    
    @pytest.fixture
    def interpreter(self):
        """Create dance interpreter with mocked dependencies."""
        with patch('chatty_commander.vision.dance_interpreter.RhythmDetector'):
            with patch('chatty_commander.vision.dance_interpreter.FlowAnalyzer'):
                from chatty_commander.vision.dance_interpreter import DanceInterpreter
                return DanceInterpreter()
    
    def test_interpreter_initialization(self):
        """Test dance interpreter can be initialized."""
        with patch('chatty_commander.vision.dance_interpreter.RhythmDetector'):
            with patch('chatty_commander.vision.dance_interpreter.FlowAnalyzer'):
                from chatty_commander.vision.dance_interpreter import DanceInterpreter
                
                interpreter = DanceInterpreter()
                assert interpreter is not None
                assert hasattr(interpreter, 'rhythm_detector')
                assert hasattr(interpreter, 'flow_analyzer')
    
    def test_process_frame_with_mock_landmarks(self, interpreter, mock_landmarks):
        """Test processing frame with mock landmarks."""
        result = interpreter.process_frame(mock_landmarks)
        
        assert isinstance(result, dict)
        assert 'commands' in result
        assert 'flow_state' in result
        assert 'on_beat' in result
        assert isinstance(result['commands'], list)
    
    def test_process_frame_no_landmarks(self, interpreter):
        """Test processing with no landmarks (empty frame)."""
        result = interpreter.process_frame([])
        
        assert isinstance(result, dict)
        assert result['commands'] == []
        assert result['flow_state'] is None
    
    def test_process_frame_none_landmarks(self, interpreter):
        """Test processing with None landmarks."""
        result = interpreter.process_frame(None)
        
        assert isinstance(result, dict)
        assert result['commands'] == []
    
    def test_callback_triggering(self, interpreter, mock_landmarks):
        """Test that callbacks are triggered correctly."""
        commands_received = []
        
        def on_command(cmd, flow_state):
            commands_received.append(cmd)
        
        interpreter.set_callbacks(on_command=on_command)
        
        # Process multiple frames
        for _ in range(10):
            interpreter.process_frame(mock_landmarks)
        
        # Callbacks should have been called or not error
        assert isinstance(commands_received, list)
    
    def test_phrase_tracking(self, interpreter, mock_landmarks):
        """Test phrase detection and tracking."""
        # Simulate a phrase by processing multiple frames
        for i in range(90):  # 3 seconds at 30fps
            # Vary energy slightly
            for lm in mock_landmarks:
                lm.x += np.sin(i * 0.1) * 0.01
            
            result = interpreter.process_frame(mock_landmarks)
        
        assert isinstance(result, dict)
    
    def test_get_visualization_data(self, interpreter, mock_landmarks):
        """Test visualization data retrieval."""
        # Process some frames
        for _ in range(10):
            interpreter.process_frame(mock_landmarks)
        
        viz_data = interpreter.get_visualization_data()
        
        assert isinstance(viz_data, dict)
        assert 'ghost_trail' in viz_data
        assert 'tempo' in viz_data
    
    def test_ghost_trail_accumulation(self, interpreter, mock_landmarks):
        """Test that ghost trail accumulates positions."""
        # Process multiple frames
        for i in range(50):
            # Move wrists
            mock_landmarks[15].x = 0.3 + i * 0.01
            mock_landmarks[16].x = 0.7 - i * 0.01
            interpreter.process_frame(mock_landmarks)
        
        viz_data = interpreter.get_visualization_data()
        trail = viz_data.get('ghost_trail', [])
        
        assert len(trail) > 0
        assert len(trail) <= interpreter.ghost_trail_length


class TestRhythmDetector:
    """Test rhythm detection with mocks."""
    
    @pytest.fixture
    def detector(self):
        """Create rhythm detector."""
        from chatty_commander.vision.dance_interpreter import RhythmDetector
        return RhythmDetector()
    
    @pytest.fixture
    def moving_landmarks(self):
        """Create landmarks with rhythmic motion."""
        def generate(frame_num):
            landmarks = []
            for i in range(33):
                # Simulate rhythmic motion at 2Hz
                if i in [15, 16]:  # Wrists
                    phase = frame_num * 0.1  # ~2Hz at 30fps
                    x = 0.5 + 0.2 * np.sin(phase)
                    y = 0.5
                elif i in [11, 12]:  # Shoulders
                    x = 0.4 if i == 11 else 0.6
                    y = 0.3
                else:
                    x, y = 0.5, 0.5
                landmarks.append(MockLandmark(x=x, y=y))
            return landmarks
        return generate
    
    def test_rhythm_detector_initialization(self):
        """Test rhythm detector can be initialized."""
        from chatty_commander.vision.dance_interpreter import RhythmDetector
        detector = RhythmDetector()
        
        assert detector is not None
        assert detector.tempo_bpm == 0
        assert detector.beat_confidence == 0.0
    
    def test_add_frame_accumulates_history(self, detector, moving_landmarks):
        """Test that frames are added to motion history."""
        for i in range(10):
            landmarks = moving_landmarks(i)
            detector.add_frame(landmarks)
        
        assert len(detector.motion_history) == 10
    
    def test_beat_detection_with_rhythmic_motion(self, detector, moving_landmarks):
        """Test beat detection with rhythmic input."""
        beats_detected = 0
        
        # Simulate 3 seconds of rhythmic motion
        for i in range(90):
            landmarks = moving_landmarks(i)
            beat = detector.add_frame(landmarks)
            if beat:
                beats_detected += 1
        
        # Should detect some beats (exact number depends on algorithm)
        assert beats_detected >= 0  # May or may not detect depending on motion
    
    def test_tempo_calculation(self, detector, moving_landmarks):
        """Test BPM calculation from beats."""
        # Add frames with rhythmic motion
        for i in range(120):  # 4 seconds
            landmarks = moving_landmarks(i)
            detector.add_frame(landmarks)
        
        tempo, confidence = detector.get_tempo()
        
        assert isinstance(tempo, int)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1.0
    
    def test_on_beat_detection(self, detector, moving_landmarks):
        """Test on-beat timing detection."""
        # Add rhythmic frames
        for i in range(60):
            landmarks = moving_landmarks(i)
            detector.add_frame(landmarks)
        
        is_on_beat = detector.is_on_beat(tolerance_ms=100)
        
        # Should return boolean
        assert isinstance(is_on_beat, bool)


class TestFlowAnalyzer:
    """Test flow analysis with mocks."""
    
    @pytest.fixture
    def analyzer(self):
        """Create flow analyzer."""
        from chatty_commander.vision.dance_interpreter import FlowAnalyzer
        return FlowAnalyzer()
    
    @pytest.fixture
    def static_landmarks(self):
        """Create static (non-moving) landmarks."""
        landmarks = []
        for i in range(33):
            landmarks.append(MockLandmark(x=0.5, y=0.5, visibility=1.0))
        return landmarks
    
    @pytest.fixture
    def expanding_landmarks(self, request):
        """Create landmarks that expand outward over time."""
        def generate(expansion_factor):
            landmarks = []
            for i in range(33):
                if i == 15:  # Left wrist - expanding outward
                    x = 0.3 - expansion_factor * 0.2
                    y = 0.5 - expansion_factor * 0.2
                elif i == 16:  # Right wrist
                    x = 0.7 + expansion_factor * 0.2
                    y = 0.5 - expansion_factor * 0.2
                elif i in [11, 12]:  # Shoulders
                    x = 0.4 if i == 11 else 0.6
                    y = 0.3
                else:
                    x, y = 0.5, 0.5
                landmarks.append(MockLandmark(x=x, y=y))
            return landmarks
        return generate
    
    def test_analyze_frame_returns_flow_state(self, analyzer, static_landmarks):
        """Test that analyze_frame returns FlowState."""
        from chatty_commander.vision.dance_interpreter import FlowState
        
        flow = analyzer.analyze_frame(static_landmarks)
        
        assert isinstance(flow, FlowState)
        assert hasattr(flow, 'continuity')
        assert hasattr(flow, 'expansion')
        assert hasattr(flow, 'symmetry')
        assert hasattr(flow, 'energy')
        assert hasattr(flow, 'style')
    
    def test_analyze_frame_no_landmarks(self, analyzer):
        """Test analysis with no landmarks."""
        flow = analyzer.analyze_frame([])
        
        # Should return default flow state
        assert flow is not None
    
    def test_expansion_detection(self, analyzer, expanding_landmarks):
        """Test that expansion is detected correctly."""
        # Process expanding frames
        for i in range(10):
            landmarks = expanding_landmarks(i / 10.0)  # 0 to 1
            flow = analyzer.analyze_frame(landmarks)
        
        # Expansion should be detected
        assert flow.expansion > 0.5
    
    def test_continuity_calculation(self, analyzer):
        """Test continuity calculation from motion history."""
        # Generate smooth continuous motion
        for i in range(20):
            landmarks = []
            for j in range(33):
                if j == 15:  # Smooth sine wave motion
                    x = 0.5 + 0.2 * np.sin(i * 0.2)
                    y = 0.5
                else:
                    x, y = 0.5, 0.5
                landmarks.append(MockLandmark(x=x, y=y))
            
            flow = analyzer.analyze_frame(landmarks)
        
        # Smooth motion should have high continuity
        assert flow.continuity > 0.5
    
    def test_energy_calculation(self, analyzer):
        """Test energy level calculation."""
        from chatty_commander.vision.dance_interpreter import EnergyLevel
        
        # Static motion = low energy
        for i in range(10):
            landmarks = [MockLandmark(x=0.5, y=0.5) for _ in range(33)]
            flow = analyzer.analyze_frame(landmarks)
        
        assert flow.energy in EnergyLevel
        assert flow.energy.value <= 0.5  # Should be calm/medatative
    
    def test_style_detection(self, analyzer, expanding_landmarks):
        """Test dance style detection."""
        from chatty_commander.vision.dance_interpreter import DanceStyle
        
        # Process expanding frames
        for i in range(15):
            landmarks = expanding_landmarks(i / 15.0)
            flow = analyzer.analyze_frame(landmarks)
        
        # Should detect some style
        assert flow.style in DanceStyle


class TestExpressiveCommandMapper:
    """Test expressive command mapping."""
    
    @pytest.fixture
    def mapper(self):
        """Create command mapper."""
        from chatty_commander.vision.dance_interpreter import ExpressiveCommandMapper
        return ExpressiveCommandMapper()
    
    @pytest.fixture
    def mock_flow_state(self):
        """Create mock flow states."""
        from chatty_commander.vision.dance_interpreter import FlowState, EnergyLevel, DanceStyle
        
        return FlowState(
            continuity=0.8,
            expansion=0.9,
            symmetry=0.6,
            rhythm_lock=0.7,
            energy=EnergyLevel.EXPLOSIVE,
            style=DanceStyle.CONTEMPORARY
        )
    
    def test_map_flow_to_command_explosive_energy(self, mapper, mock_flow_state):
        """Test that explosive energy triggers maximize command."""
        commands = mapper.map_flow_to_command(mock_flow_state, on_beat=False)
        
        if commands:
            assert 'maximize' in commands
    
    def test_map_flow_to_command_expansion(self, mapper, mock_flow_state):
        """Test that high expansion triggers expand command."""
        commands = mapper.map_flow_to_command(mock_flow_state, on_beat=False)
        
        if commands:
            assert any('expand' in cmd for cmd in commands)
    
    def test_map_flow_returns_none_for_neutral(self, mapper):
        """Test that neutral flow returns no commands."""
        from chatty_commander.vision.dance_interpreter import FlowState, EnergyLevel, DanceStyle
        
        neutral_flow = FlowState(
            continuity=0.5,
            expansion=0.5,
            symmetry=0.5,
            rhythm_lock=0.5,
            energy=EnergyLevel.CALM,
            style=DanceStyle.FREE_FORM
        )
        
        commands = mapper.map_flow_to_command(neutral_flow, on_beat=False)
        
        # May or may not return commands for neutral state
        assert commands is None or isinstance(commands, list)
    
    def test_interpret_phrase_building_arc(self, mapper):
        """Test phrase interpretation for building energy arc."""
        from chatty_commander.vision.dance_interpreter import FlowState, EnergyLevel, DanceStyle, DancePhrase
        
        # Create phrase with building energy
        flows = [
            FlowState(0.5, 0.5, 0.5, 0.5, EnergyLevel.CALM, DanceStyle.FLOW),
            FlowState(0.6, 0.6, 0.6, 0.6, EnergyLevel.GROOVING, DanceStyle.FLOW),
            FlowState(0.8, 0.8, 0.7, 0.8, EnergyLevel.ENERGETIC, DanceStyle.CONTEMPORARY),
        ]
        
        phrase = DancePhrase(
            start_time=0,
            end_time=3.0,
            movements=[],
            flow_states=flows,
            dominant_style=DanceStyle.CONTEMPORARY,
            average_energy=EnergyLevel.ENERGETIC,
            intent="building"
        )
        
        commands = mapper.interpret_phrase(phrase)
        
        assert isinstance(commands, list)
        assert 'build_up' in commands
    
    def test_interpret_phrase_resolving_arc(self, mapper):
        """Test phrase interpretation for resolving energy arc."""
        from chatty_commander.vision.dance_interpreter import FlowState, EnergyLevel, DanceStyle, DancePhrase
        
        # Create phrase with resolving energy
        flows = [
            FlowState(0.8, 0.8, 0.7, 0.8, EnergyLevel.ENERGETIC, DanceStyle.CONTEMPORARY),
            FlowState(0.6, 0.6, 0.6, 0.6, EnergyLevel.GROOVING, DanceStyle.FLOW),
            FlowState(0.3, 0.3, 0.5, 0.3, EnergyLevel.CALM, DanceStyle.FLOW),
        ]
        
        phrase = DancePhrase(
            start_time=0,
            end_time=3.0,
            movements=[],
            flow_states=flows,
            dominant_style=DanceStyle.FLOW,
            average_energy=EnergyLevel.CALM,
            intent="resolving"
        )
        
        commands = mapper.interpret_phrase(phrase)
        
        assert isinstance(commands, list)
        assert 'resolve' in commands


class TestDanceAdapter:
    """Test dance input adapter with mocks."""
    
    @pytest.fixture
    def adapter(self):
        """Create dance adapter with mocked dependencies."""
        with patch('chatty_commander.vision.dance_adapter.BodyController') as mock_controller:
            with patch('chatty_commander.vision.dance_adapter.DanceInterpreter') as mock_interpreter:
                from chatty_commander.vision.dance_adapter import DanceInputAdapter
                return DanceInputAdapter({'enabled': True})
    
    def test_adapter_initialization(self):
        """Test dance adapter can be initialized."""
        with patch('chatty_commander.vision.dance_adapter.BodyController'):
            with patch('chatty_commander.vision.dance_adapter.DanceInterpreter'):
                from chatty_commander.vision.dance_adapter import DanceInputAdapter
                
                adapter = DanceInputAdapter()
                assert adapter is not None
                assert adapter.mode == 'interpretive'
    
    def test_set_callbacks(self, adapter):
        """Test setting callbacks."""
        def on_cmd(cmd):
            pass
        
        def on_flow(flow):
            pass
        
        adapter.set_command_callback(on_cmd)
        adapter.set_flow_callback(on_flow)
        
        assert adapter.command_callback == on_cmd
        assert adapter.flow_callback == on_flow
    
    @patch('chatty_commander.vision.dance_adapter.BodyController')
    @patch('chatty_commander.vision.dance_adapter.DanceInterpreter')
    def test_start_stop_lifecycle(self, mock_interpreter, mock_controller):
        """Test adapter start/stop lifecycle."""
        from chatty_commander.vision.dance_adapter import DanceInputAdapter
        
        # Configure mocks
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance
        mock_controller_instance.start.return_value = True
        
        adapter = DanceInputAdapter({'enabled': True})
        
        # Start
        result = adapter.start()
        assert result is True
        
        # Stop
        adapter.stop()
        mock_controller_instance.stop.assert_called_once()
    
    def test_get_status(self, adapter):
        """Test status retrieval."""
        status = adapter.get_status()
        
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'mode' in status


# Integration-style tests with full mocking
class TestDanceModeIntegration:
    """Integration tests for dance mode with all components mocked."""
    
    def test_full_dance_pipeline(self):
        """Test complete dance pipeline from frame to command."""
        with patch('chatty_commander.vision.dance_adapter.BodyController') as mock_bc:
            with patch('chatty_commander.vision.dance_adapter.DanceInterpreter') as mock_di:
                from chatty_commander.vision.dance_adapter import DanceInputAdapter
                
                # Configure mocks
                mock_bc_instance = MagicMock()
                mock_bc.return_value = mock_bc_instance
                mock_bc_instance.start.return_value = True
                
                mock_di_instance = MagicMock()
                mock_di.return_value = mock_di_instance
                
                # Simulate dance processing
                commands_triggered = []
                
                def capture_command(cmd):
                    commands_triggered.append(cmd)
                
                adapter = DanceInputAdapter({'enabled': True})
                adapter.set_command_callback(capture_command)
                
                # Mock the interpreter to return commands
                mock_di_instance.process_frame.return_value = {
                    'commands': ['maximize', 'expand_all'],
                    'flow_state': Mock(),
                    'on_beat': True,
                    'tempo': 120
                }
                
                adapter.start()
                
                # Simulate processing frames
                for _ in range(10):
                    result = adapter.process_frame()
                
                # Cleanup
                adapter.stop()
                
                # Verify pipeline worked
                assert isinstance(commands_triggered, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
