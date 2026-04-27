"""
Mock tests for body controller and gesture system.

Tests without requiring:
- Actual camera hardware
- MediaPipe installation
- OpenCV display capabilities
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from dataclasses import dataclass
import time


@dataclass
class MockLandmark:
    """Mock MediaPipe landmark."""
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


class TestGestureTrainer:
    """Test gesture trainer with mocks."""
    
    @pytest.fixture
    def trainer(self, tmp_path):
        """Create gesture trainer with temp config."""
        from chatty_commander.vision.body_controller import GestureTrainer
        config_path = tmp_path / "gestures.json"
        return GestureTrainer(config_path=config_path)
    
    def test_trainer_initialization(self, trainer):
        """Test trainer can be initialized."""
        assert trainer is not None
        assert trainer.min_frames == 10
        assert trainer.max_frames == 60
    
    def test_list_gestures_empty(self, trainer):
        """Test listing gestures when none exist."""
        gestures = trainer.list_gestures()
        assert isinstance(gestures, list)
        assert len(gestures) == 0
    
    def test_map_gesture_to_command(self, trainer):
        """Test mapping gesture to command."""
        trainer.map_gesture_to_command('wave', 'next_track')
        
        assert 'wave' in trainer.gesture_mappings
        assert trainer.gesture_mappings['wave'] == 'next_track'
    
    def test_get_command_for_gesture(self, trainer):
        """Test retrieving command for gesture."""
        trainer.map_gesture_to_command('thumbs_up', 'volume_up')
        
        command = trainer.get_command_for_gesture('thumbs_up')
        assert command == 'volume_up'
    
    def test_get_command_for_unknown_gesture(self, trainer):
        """Test retrieving command for unknown gesture."""
        command = trainer.get_command_for_gesture('unknown')
        assert command is None
    
    def test_delete_gesture(self, trainer):
        """Test deleting a gesture."""
        from chatty_commander.vision.body_controller import GestureSample
        
        # Add a gesture
        trainer.gesture_samples['test_gesture'] = []
        trainer.gesture_mappings['test_gesture'] = 'test_command'
        
        # Delete it
        result = trainer.delete_gesture('test_gesture')
        
        assert result is True
        assert 'test_gesture' not in trainer.gesture_samples
        assert 'test_gesture' not in trainer.gesture_mappings
    
    def test_delete_nonexistent_gesture(self, trainer):
        """Test deleting non-existent gesture."""
        result = trainer.delete_gesture('nonexistent')
        assert result is False
    
    def test_start_recording(self, trainer):
        """Test starting a recording session."""
        progress_calls = []
        
        def progress_callback(progress, frames):
            progress_calls.append((progress, frames))
        
        trainer.start_recording('test_gesture', duration=1.0, callback=progress_callback)
        
        assert hasattr(trainer, '_current_recording')
        assert trainer._current_recording['name'] == 'test_gesture'
    
    def test_add_frame_to_recording(self, trainer):
        """Test adding frames to recording."""
        trainer.start_recording('test_gesture', duration=2.0)
        
        # Add some frames
        landmarks = [MockLandmark(x=0.5, y=0.5) for _ in range(33)]
        
        for i in range(5):
            is_complete = trainer.add_frame(landmarks)
        
        # Should have frames accumulated
        assert len(trainer._current_recording['frames']) == 5


class TestBodyWireframeDetector:
    """Test body wireframe detector with mocks."""
    
    @pytest.fixture
    def detector(self):
        """Create detector with mocked MediaPipe."""
        with patch('chatty_commander.vision.body_controller.MEDIAPIPE_AVAILABLE', True):
            with patch('chatty_commander.vision.body_controller.mp_pose') as mock_mp:
                mock_pose = MagicMock()
                mock_mp.Pose.return_value = mock_pose
                
                from chatty_commander.vision.body_controller import BodyWireframeDetector
                return BodyWireframeDetector()
    
    def test_detector_initialization(self):
        """Test detector can be initialized."""
        with patch('chatty_commander.vision.body_controller.MEDIAPIPE_AVAILABLE', True):
            with patch('chatty_commander.vision.body_controller.mp_pose'):
                from chatty_commander.vision.body_controller import BodyWireframeDetector
                
                detector = BodyWireframeDetector()
                assert detector is not None
                assert detector.min_detection_confidence == 0.5
    
    @patch('chatty_commander.vision.body_controller.MEDIAPIPE_AVAILABLE', True)
    def test_detect_with_mock_results(self):
        """Test detection with mock MediaPipe results."""
        with patch('chatty_commander.vision.body_controller.mp_pose') as mock_mp:
            with patch('chatty_commander.vision.body_controller.mp_drawing'):
                with patch('chatty_commander.vision.body_controller.mp_drawing_styles'):
                    mock_pose = MagicMock()
                    
                    # Mock detection results
                    mock_results = MagicMock()
                    mock_results.pose_landmarks = MagicMock()
                    mock_results.pose_landmarks.landmark = [
                        MagicMock(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(33)
                    ]
                    mock_pose.process.return_value = mock_results
                    mock_mp.Pose.return_value = mock_pose
                    
                    from chatty_commander.vision.body_controller import BodyWireframeDetector
                    import numpy as np
                    
                    detector = BodyWireframeDetector()
                    detector.pose = mock_pose
                    
                    # Create test frame
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    
                    annotated_frame, landmarks = detector.detect(frame)
                    
                    assert landmarks is not None
                    assert len(landmarks) == 33
    
    @patch('chatty_commander.vision.body_controller.MEDIAPIPE_AVAILABLE', False)
    def test_mock_detect_fallback(self):
        """Test fallback when MediaPipe unavailable."""
        from chatty_commander.vision.body_controller import BodyWireframeDetector
        import numpy as np
        
        detector = BodyWireframeDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        annotated_frame, landmarks = detector.detect(frame)
        
        # Should return frame and None landmarks in mock mode
        assert landmarks is None
    
    def test_get_landmark_name(self):
        """Test landmark name retrieval."""
        with patch('chatty_commander.vision.body_controller.MEDIAPIPE_AVAILABLE', False):
            from chatty_commander.vision.body_controller import BodyWireframeDetector
            
            detector = BodyWireframeDetector()
            
            name = detector.get_landmark_name(0)
            assert name == 'nose'
            
            name = detector.get_landmark_name(15)
            assert name == 'left_wrist'
            
            name = detector.get_landmark_name(100)
            assert name == 'landmark_100'


class TestGestureRecognizer:
    """Test gesture recognizer with mocks."""
    
    @pytest.fixture
    def mock_trainer(self):
        """Create mock gesture trainer."""
        trainer = MagicMock()
        trainer.gesture_samples = {}
        trainer.min_frames = 10
        return trainer
    
    @pytest.fixture
    def recognizer(self, mock_trainer):
        """Create gesture recognizer."""
        from chatty_commander.vision.body_controller import GestureRecognizer
        return GestureRecognizer(mock_trainer)
    
    def test_recognizer_initialization(self, recognizer):
        """Test recognizer can be initialized."""
        assert recognizer is not None
        assert recognizer.confidence_threshold == 0.75
    
    def test_process_frame_no_gestures(self, recognizer):
        """Test processing frame with no trained gestures."""
        landmarks = [MockLandmark(x=0.5, y=0.5) for _ in range(33)]
        
        result = recognizer.process_frame(landmarks)
        
        assert result is None
    
    def test_process_frame_insufficient_buffer(self, recognizer):
        """Test processing with insufficient buffer."""
        # Add a trained gesture
        from chatty_commander.vision.body_controller import GestureSample, GestureFrame
        
        frames = [GestureFrame(timestamp=i*0.033, landmarks=[], frame_number=i) for i in range(5)]
        sample = GestureSample(name='wave', frames=frames, duration=1.0, metadata={})
        recognizer.trainer.gesture_samples = {'wave': [sample]}
        
        landmarks = [MockLandmark(x=0.5, y=0.5) for _ in range(33)]
        
        # Process only a few frames (not enough for matching)
        for _ in range(5):
            result = recognizer.process_frame(landmarks)
        
        # Should return None (insufficient buffer)
        assert result is None
    
    def test_reset_buffer(self, recognizer):
        """Test buffer reset."""
        # Add some frames to buffer
        landmarks = [MockLandmark(x=0.5, y=0.5) for _ in range(33)]
        for _ in range(10):
            recognizer.process_frame(landmarks)
        
        assert len(recognizer.detection_buffer) > 0
        
        # Reset
        recognizer.reset_buffer()
        
        assert len(recognizer.detection_buffer) == 0


class TestBodyController:
    """Test body controller with mocks."""
    
    @pytest.fixture
    def controller(self):
        """Create controller with mocked components."""
        with patch('chatty_commander.vision.body_controller.BodyWireframeDetector'):
            with patch('chatty_commander.vision.body_controller.GestureTrainer'):
                with patch('chatty_commander.vision.body_controller.GestureRecognizer'):
                    from chatty_commander.vision.body_controller import BodyController
                    return BodyController()
    
    def test_controller_initialization(self):
        """Test controller can be initialized."""
        with patch('chatty_commander.vision.body_controller.BodyWireframeDetector'):
            with patch('chatty_commander.vision.body_controller.GestureTrainer'):
                with patch('chatty_commander.vision.body_controller.GestureRecognizer'):
                    from chatty_commander.vision.body_controller import BodyController
                    
                    controller = BodyController()
                    assert controller is not None
    
    @patch('chatty_commander.vision.body_controller.BodyWireframeDetector')
    @patch('chatty_commander.vision.body_controller.GestureTrainer')
    @patch('chatty_commander.vision.body_controller.GestureRecognizer')
    @patch('cv2.VideoCapture')
    def test_start_stop_lifecycle(self, mock_vc, mock_rec, mock_trainer, mock_detector):
        """Test controller start/stop lifecycle."""
        from chatty_commander.vision.body_controller import BodyController
        
        # Configure mock
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_vc.return_value = mock_cap
        
        controller = BodyController()
        
        # Start
        result = controller.start(camera_index=0)
        assert result is True
        
        # Stop
        controller.stop()
        mock_cap.release.assert_called_once()
    
    @patch('chatty_commander.vision.body_controller.BodyWireframeDetector')
    @patch('chatty_commander.vision.body_controller.GestureTrainer')
    @patch('chatty_commander.vision.body_controller.GestureRecognizer')
    def test_start_failure_no_camera(self, mock_rec, mock_trainer, mock_detector):
        """Test handling when camera unavailable."""
        from chatty_commander.vision.body_controller import BodyController
        
        with patch('cv2.VideoCapture') as mock_vc:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = False
            mock_vc.return_value = mock_cap
            
            controller = BodyController()
            result = controller.start(camera_index=0)
            
            assert result is False
    
    def test_set_callbacks(self, controller):
        """Test setting callbacks."""
        def cmd_callback(cmd):
            pass
        
        def frame_callback(frame):
            pass
        
        def detection_callback(gesture):
            pass
        
        controller.set_command_callback(cmd_callback)
        controller.set_frame_callback(frame_callback)
        controller.set_detection_callback(detection_callback)
        
        assert controller.command_callback == cmd_callback
        assert controller.frame_callback == frame_callback
        assert controller.detection_callback == detection_callback
    
    def test_list_gestures(self, controller):
        """Test listing trained gestures."""
        # Mock trainer
        controller.trainer.list_gestures.return_value = ['wave', 'thumbs_up']
        
        gestures = controller.list_gestures()
        
        assert isinstance(gestures, list)
        assert 'wave' in gestures
    
    def test_map_gesture(self, controller):
        """Test mapping gesture to command."""
        controller.map_gesture('wave', 'next_track')
        controller.trainer.map_gesture_to_command.assert_called_once_with('wave', 'next_track')
    
    def test_get_status(self, controller):
        """Test status retrieval."""
        status = controller.get_status()
        
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'gestures_trained' in status


class TestGestureInputAdapter:
    """Test gesture input adapter with mocks."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked body controller."""
        with patch('chatty_commander.vision.gesture_adapter.BodyController'):
            from chatty_commander.vision.gesture_adapter import GestureInputAdapter
            return GestureInputAdapter({'enabled': True})
    
    def test_adapter_initialization(self):
        """Test adapter can be initialized."""
        with patch('chatty_commander.vision.gesture_adapter.BodyController'):
            from chatty_commander.vision.gesture_adapter import GestureInputAdapter
            
            adapter = GestureInputAdapter()
            assert adapter is not None
            assert adapter.enabled is True
    
    def test_set_command_callback(self, adapter):
        """Test setting command callback."""
        def callback(cmd):
            pass
        
        adapter.set_command_callback(callback)
        assert adapter.command_callback == callback
    
    @patch('chatty_commander.vision.gesture_adapter.BodyController')
    def test_start_stop(self, mock_bc):
        """Test adapter start/stop."""
        from chatty_commander.vision.gesture_adapter import GestureInputAdapter
        
        # Configure mock
        mock_controller = MagicMock()
        mock_controller.start.return_value = True
        mock_bc.return_value = mock_controller
        
        adapter = GestureInputAdapter({'enabled': True, 'camera_index': 0})
        adapter.set_command_callback(lambda x: None)
        
        result = adapter.start()
        assert result is True
        
        adapter.stop()
        mock_controller.stop.assert_called_once()
    
    def test_train_gesture(self, adapter):
        """Test training a gesture."""
        adapter._is_started = True
        adapter.body_controller.train_gesture = MagicMock(return_value=True)
        
        result = adapter.train_gesture('wave', duration=1.0)
        
        assert result is True
        adapter.body_controller.train_gesture.assert_called_once()
    
    def test_map_gesture_to_command(self, adapter):
        """Test mapping gesture to command."""
        adapter.body_controller.map_gesture = MagicMock()
        
        adapter.map_gesture_to_command('wave', 'next_track')
        
        adapter.body_controller.map_gesture.assert_called_once_with('wave', 'next_track')
    
    def test_get_gesture_mappings(self, adapter):
        """Test getting gesture mappings."""
        adapter.trainer = MagicMock()
        adapter.trainer.gesture_mappings = {'wave': 'next_track'}
        
        mappings = adapter.get_gesture_mappings()
        
        assert isinstance(mappings, dict)
        assert mappings['wave'] == 'next_track'
    
    def test_get_status(self, adapter):
        """Test status retrieval."""
        adapter.body_controller.get_status = MagicMock(return_value={
            'is_running': False,
            'gestures_trained': 5
        })
        
        status = adapter.get_status()
        
        assert isinstance(status, dict)
        assert status['enabled'] is True


class TestGestureCommandMapper:
    """Test gesture command mapper with mocks."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock gesture adapter."""
        adapter = MagicMock()
        adapter.trainer = MagicMock()
        return adapter
    
    @pytest.fixture
    def mapper(self, mock_adapter):
        """Create gesture command mapper."""
        from chatty_commander.vision.gesture_adapter import GestureCommandMapper
        return GestureCommandMapper(mock_adapter)
    
    def test_mapper_initialization(self, mapper):
        """Test mapper can be initialized."""
        assert mapper is not None
        assert len(mapper.DEFAULT_GESTURES) == 10
    
    def test_setup_defaults(self, mapper, mock_adapter):
        """Test setting up default gestures."""
        mapper.setup_defaults()
        
        # Should have mapped all default gestures
        assert mock_adapter.map_gesture_to_command.call_count == 10
    
    def test_get_gesture_guide(self, mapper):
        """Test getting gesture guide."""
        guide = mapper.get_gesture_guide()
        
        assert isinstance(guide, dict)
        assert 'wave_right' in guide
        assert 'thumbs_up' in guide
    
    def test_print_gesture_guide(self, mapper, capsys):
        """Test printing gesture guide."""
        mapper.print_gesture_guide()
        
        captured = capsys.readouterr()
        assert 'CHATTY COMMANDER GESTURE GUIDE' in captured.out
        assert 'wave_right' in captured.out


# Integration test with all components mocked
class TestGestureSystemIntegration:
    """Integration tests for complete gesture system."""
    
    @patch('chatty_commander.vision.gesture_adapter.BodyController')
    def test_full_gesture_pipeline(self, mock_bc):
        """Test complete gesture recognition pipeline."""
        from chatty_commander.vision.gesture_adapter import GestureInputAdapter, create_gesture_adapter
        
        # Configure mocks
        mock_controller = MagicMock()
        mock_controller.start.return_value = True
        mock_controller.list_gestures.return_value = ['wave', 'thumbs_up']
        mock_controller.trainer = MagicMock()
        mock_controller.trainer.gesture_mappings = {'wave': 'next_track'}
        mock_bc.return_value = mock_controller
        
        # Create adapter
        adapter = create_gesture_adapter({'enabled': True})
        
        # Track commands
        commands_received = []
        adapter.set_command_callback(lambda cmd: commands_received.append(cmd))
        
        # Start
        result = adapter.start()
        assert result is True
        
        # Verify gesture list
        gestures = adapter.list_trained_gestures()
        assert 'wave' in gestures
        
        # Verify mappings
        mappings = adapter.get_gesture_mappings()
        assert mappings['wave'] == 'next_track'
        
        # Stop
        adapter.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
