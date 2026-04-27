"""
OpenCV Body Wireframe Detection for Gesture-Based Input Control.

Uses MediaPipe for real-time pose detection and gesture classification.
Supports training custom gestures and mapping them to Chatty Commander commands.
"""

import cv2
import numpy as np
import logging
import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import deque
import threading

logger = logging.getLogger(__name__)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available. Body controller will use mock data.")


@dataclass
class BodyLandmark:
    """Represents a single body landmark with 3D coordinates."""
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class GestureFrame:
    """A single frame of body pose data."""
    timestamp: float
    landmarks: List[BodyLandmark]
    frame_number: int


@dataclass
class GestureSample:
    """A complete gesture sample with multiple frames."""
    name: str
    frames: List[GestureFrame]
    duration: float
    metadata: Dict[str, Any]


@dataclass
class DetectedGesture:
    """Result of gesture detection."""
    name: str
    confidence: float
    landmarks: List[BodyLandmark]
    timestamp: float


class GestureTrainer:
    """
    Train and manage custom gestures for body control.
    
    Collects gesture samples, trains classification models,
    and manages gesture-to-command mappings.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize gesture trainer with optional config path."""
        self.config_path = config_path or Path("~/.chatty_commander/gestures.json").expanduser()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.gesture_samples: Dict[str, List[GestureSample]] = {}
        self.gesture_mappings: Dict[str, str] = {}  # gesture_name -> command
        self.min_frames = 10
        self.max_frames = 60
        self.similarity_threshold = 0.85
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load gesture configuration from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.gesture_mappings = data.get('mappings', {})
                    logger.info(f"Loaded {len(self.gesture_mappings)} gesture mappings")
            except Exception as e:
                logger.error(f"Failed to load gesture config: {e}")
    
    def _save_config(self) -> None:
        """Save gesture configuration to disk."""
        try:
            data = {
                'mappings': self.gesture_mappings,
                'version': '1.0',
                'updated': time.time()
            }
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved gesture config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save gesture config: {e}")
    
    def start_recording(
        self, 
        gesture_name: str, 
        duration: float = 2.0,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Start recording a gesture sample.
        
        Args:
            gesture_name: Name of the gesture to record
            duration: Recording duration in seconds
            callback: Optional callback for progress updates
        """
        logger.info(f"Starting gesture recording: {gesture_name} ({duration}s)")
        
        # This will be called by the BodyController during recording
        self._current_recording = {
            'name': gesture_name,
            'start_time': time.time(),
            'duration': duration,
            'frames': [],
            'callback': callback
        }
    
    def add_frame(self, landmarks: List[BodyLandmark]) -> bool:
        """
        Add a frame to the current recording.
        
        Returns:
            True if recording is complete, False otherwise
        """
        if not hasattr(self, '_current_recording'):
            return False
        
        recording = self._current_recording
        elapsed = time.time() - recording['start_time']
        
        if elapsed >= recording['duration']:
            # Recording complete
            self._finish_recording()
            return True
        
        # Add frame
        frame = GestureFrame(
            timestamp=elapsed,
            landmarks=landmarks,
            frame_number=len(recording['frames'])
        )
        recording['frames'].append(frame)
        
        # Progress callback
        if recording['callback']:
            progress = elapsed / recording['duration']
            recording['callback'](progress, len(recording['frames']))
        
        return False
    
    def _finish_recording(self) -> GestureSample:
        """Finish recording and save the gesture sample."""
        recording = self._current_recording
        
        sample = GestureSample(
            name=recording['name'],
            frames=recording['frames'],
            duration=time.time() - recording['start_time'],
            metadata={'recorded_at': time.time()}
        )
        
        # Save to samples
        if sample.name not in self.gesture_samples:
            self.gesture_samples[sample.name] = []
        self.gesture_samples[sample.name].append(sample)
        
        logger.info(f"Recorded gesture '{sample.name}' with {len(sample.frames)} frames")
        
        delattr(self, '_current_recording')
        return sample
    
    def map_gesture_to_command(self, gesture_name: str, command: str) -> None:
        """
        Map a gesture name to a Chatty Commander command.
        
        Args:
            gesture_name: Name of the trained gesture
            command: Chatty Commander command to execute
        """
        self.gesture_mappings[gesture_name] = command
        self._save_config()
        logger.info(f"Mapped gesture '{gesture_name}' to command '{command}'")
    
    def get_command_for_gesture(self, gesture_name: str) -> Optional[str]:
        """Get the command mapped to a gesture."""
        return self.gesture_mappings.get(gesture_name)
    
    def list_gestures(self) -> List[str]:
        """List all trained gesture names."""
        return list(self.gesture_samples.keys())
    
    def delete_gesture(self, gesture_name: str) -> bool:
        """Delete a gesture and its mappings."""
        if gesture_name in self.gesture_samples:
            del self.gesture_samples[gesture_name]
            if gesture_name in self.gesture_mappings:
                del self.gesture_mappings[gesture_name]
                self._save_config()
            logger.info(f"Deleted gesture '{gesture_name}'")
            return True
        return False


class BodyWireframeDetector:
    """
    Real-time body wireframe detection using OpenCV and MediaPipe.
    
    Detects 33 body landmarks and renders wireframe overlay.
    """
    
    # 33 MediaPipe pose landmarks
    LANDMARK_NAMES = [
        'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
        'right_eye_inner', 'right_eye', 'right_eye_outer',
        'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
        'left_index', 'right_index', 'left_thumb', 'right_thumb',
        'left_hip', 'right_hip', 'left_knee', 'right_knee',
        'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]
    
    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1,
        enable_segmentation: bool = False
    ):
        """Initialize body wireframe detector."""
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        self.enable_segmentation = enable_segmentation
        
        self.pose = None
        self._initialize_pose()
        
        # Visualization settings
        self.wireframe_color = (0, 255, 0)  # Green
        self.joint_color = (0, 0, 255)  # Red
        self.wireframe_thickness = 2
        self.joint_radius = 4
        
        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.last_frame_time = time.time()
    
    def _initialize_pose(self) -> None:
        """Initialize MediaPipe pose estimator."""
        if MEDIAPIPE_AVAILABLE:
            self.pose = mp_pose.Pose(
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                model_complexity=self.model_complexity,
                enable_segmentation=self.enable_segmentation
            )
            logger.info("MediaPipe Pose initialized")
        else:
            logger.warning("MediaPipe not available, using mock pose detector")
    
    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[List[BodyLandmark]]]:
        """
        Detect body pose in frame and return annotated frame + landmarks.
        
        Args:
            frame: OpenCV BGR image
            
        Returns:
            Tuple of (annotated_frame, landmarks or None)
        """
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return self._mock_detect(frame)
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(rgb_frame)
        
        # Calculate FPS
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_frame_time)
        self.fps_history.append(fps)
        self.last_frame_time = current_time
        
        landmarks = None
        
        if results.pose_landmarks:
            # Extract landmarks
            landmarks = self._extract_landmarks(results.pose_landmarks)
            
            # Draw wireframe
            annotated_frame = self._draw_wireframe(frame, results.pose_landmarks)
            
            # Draw FPS
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            cv2.putText(
                annotated_frame,
                f"FPS: {avg_fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            
            return annotated_frame, landmarks
        
        return frame, None
    
    def _extract_landmarks(self, pose_landmarks) -> List[BodyLandmark]:
        """Extract landmarks from MediaPipe results."""
        landmarks = []
        for landmark in pose_landmarks.landmark:
            landmarks.append(BodyLandmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility
            ))
        return landmarks
    
    def _draw_wireframe(self, frame: np.ndarray, pose_landmarks) -> np.ndarray:
        """Draw body wireframe on frame."""
        annotated_frame = frame.copy()
        
        # Draw connections
        mp_drawing.draw_landmarks(
            annotated_frame,
            pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return annotated_frame
    
    def _mock_detect(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[List[BodyLandmark]]]:
        """Mock detection when MediaPipe unavailable."""
        # Add text indicating mock mode
        cv2.putText(
            frame,
            "MOCK MODE - MediaPipe unavailable",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )
        return frame, None
    
    def get_landmark_name(self, index: int) -> str:
        """Get name of landmark by index."""
        if 0 <= index < len(self.LANDMARK_NAMES):
            return self.LANDMARK_NAMES[index]
        return f"landmark_{index}"
    
    def release(self) -> None:
        """Release resources."""
        if self.pose:
            self.pose.close()


class GestureRecognizer:
    """
    Recognize trained gestures from live body pose data.
    
    Uses dynamic time warping (DTW) for gesture matching.
    """
    
    def __init__(self, trainer: GestureTrainer):
        """Initialize with gesture trainer."""
        self.trainer = trainer
        self.detection_buffer: deque = deque(maxlen=30)  # 1 second at 30fps
        self.confidence_threshold = 0.75
        self.cooldown_seconds = 1.0
        self.last_detection_time = 0
    
    def process_frame(self, landmarks: List[BodyLandmark]) -> Optional[DetectedGesture]:
        """
        Process a frame and detect gestures.
        
        Args:
            landmarks: Current body landmarks
            
        Returns:
            DetectedGesture if gesture recognized, None otherwise
        """
        # Add to buffer
        self.detection_buffer.append({
            'timestamp': time.time(),
            'landmarks': landmarks
        })
        
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_detection_time < self.cooldown_seconds:
            return None
        
        # Try to match gestures
        best_match = None
        best_confidence = 0
        
        for gesture_name, samples in self.trainer.gesture_samples.items():
            for sample in samples:
                confidence = self._calculate_similarity(
                    list(self.detection_buffer),
                    sample.frames
                )
                
                if confidence > best_confidence and confidence >= self.confidence_threshold:
                    best_confidence = confidence
                    best_match = gesture_name
        
        if best_match:
            self.last_detection_time = current_time
            return DetectedGesture(
                name=best_match,
                confidence=best_confidence,
                landmarks=landmarks,
                timestamp=current_time
            )
        
        return None
    
    def _calculate_similarity(
        self,
        buffer: List[Dict],
        sample_frames: List[GestureFrame]
    ) -> float:
        """
        Calculate similarity between buffer and gesture sample.
        
        Uses simplified DTW-like matching on key landmarks (wrists, elbows, shoulders).
        """
        if len(buffer) < self.trainer.min_frames:
            return 0.0
        
        # Use key landmarks for matching: wrists (15, 16), elbows (13, 14), shoulders (11, 12)
        key_indices = [11, 12, 13, 14, 15, 16]
        
        total_distance = 0
        comparisons = 0
        
        # Sample frames for comparison
        step = max(1, len(buffer) // len(sample_frames))
        
        for i, sample_frame in enumerate(sample_frames):
            if i * step >= len(buffer):
                break
            
            buffer_frame = buffer[i * step]
            
            for idx in key_indices:
                if idx < len(sample_frame.landmarks) and idx < len(buffer_frame['landmarks']):
                    sample_lm = sample_frame.landmarks[idx]
                    buffer_lm = buffer_frame['landmarks'][idx]
                    
                    # Euclidean distance
                    distance = np.sqrt(
                        (sample_lm.x - buffer_lm.x) ** 2 +
                        (sample_lm.y - buffer_lm.y) ** 2
                    )
                    
                    total_distance += distance
                    comparisons += 1
        
        if comparisons == 0:
            return 0.0
        
        # Convert distance to confidence (inverse relationship)
        avg_distance = total_distance / comparisons
        confidence = max(0, 1 - avg_distance * 2)  # Scale factor
        
        return confidence
    
    def reset_buffer(self) -> None:
        """Clear the detection buffer."""
        self.detection_buffer.clear()


class BodyController:
    """
    Main controller for body gesture input to Chatty Commander.
    
    Integrates detection, training, recognition, and command execution.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize body controller with configuration."""
        self.config = config or {}
        
        # Initialize components
        self.detector = BodyWireframeDetector(
            min_detection_confidence=self.config.get('min_detection_confidence', 0.5),
            min_tracking_confidence=self.config.get('min_tracking_confidence', 0.5)
        )
        self.trainer = GestureTrainer(
            config_path=Path(self.config.get('gesture_config_path', '~/.chatty_commander/gestures.json'))
        )
        self.recognizer = GestureRecognizer(self.trainer)
        
        # State
        self.is_running = False
        self.command_callback: Optional[Callable[[str], None]] = None
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self.detection_callback: Optional[Callable[[DetectedGesture], None]] = None
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._capture: Optional[cv2.VideoCapture] = None
    
    def set_command_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for when gesture triggers a command."""
        self.command_callback = callback
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Set callback for each processed frame (for UI display)."""
        self.frame_callback = callback
    
    def set_detection_callback(self, callback: Callable[[DetectedGesture], None]) -> None:
        """Set callback for when gesture is detected."""
        self.detection_callback = callback
    
    def start(self, camera_index: int = 0) -> bool:
        """
        Start body controller with specified camera.
        
        Args:
            camera_index: OpenCV camera index (0 for default)
            
        Returns:
            True if started successfully
        """
        if self.is_running:
            logger.warning("Body controller already running")
            return False
        
        # Open camera
        self._capture = cv2.VideoCapture(camera_index)
        if not self._capture.isOpened():
            logger.error(f"Failed to open camera {camera_index}")
            return False
        
        self.is_running = True
        
        # Start processing thread
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"Body controller started with camera {camera_index}")
        return True
    
    def stop(self) -> None:
        """Stop body controller."""
        self.is_running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        if self._capture:
            self._capture.release()
        
        self.detector.release()
        
        logger.info("Body controller stopped")
    
    def _process_loop(self) -> None:
        """Main processing loop (runs in separate thread)."""
        while self.is_running:
            ret, frame = self._capture.read()
            if not ret:
                logger.warning("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Detect pose
            annotated_frame, landmarks = self.detector.detect(frame)
            
            # Process landmarks if detected
            if landmarks:
                # Check for gestures
                gesture = self.recognizer.process_frame(landmarks)
                
                if gesture:
                    # Trigger detection callback
                    if self.detection_callback:
                        self.detection_callback(gesture)
                    
                    # Execute mapped command
                    command = self.trainer.get_command_for_gesture(gesture.name)
                    if command and self.command_callback:
                        logger.info(f"Executing command '{command}' from gesture '{gesture.name}'")
                        self.command_callback(command)
            
            # Frame callback for UI
            if self.frame_callback:
                self.frame_callback(annotated_frame)
            
            # Small delay to prevent CPU overload
            time.sleep(0.01)
    
    def train_gesture(
        self,
        gesture_name: str,
        duration: float = 2.0,
        progress_callback: Optional[Callable[[float, int], None]] = None
    ) -> bool:
        """
        Train a new gesture from live camera input.
        
        Args:
            gesture_name: Name for the new gesture
            duration: Recording duration in seconds
            progress_callback: Callback(progress_ratio, frame_count)
            
        Returns:
            True if training successful
        """
        if not self.is_running:
            logger.error("Cannot train: Body controller not running")
            return False
        
        logger.info(f"Training gesture '{gesture_name}' for {duration}s")
        
        # Start recording
        self.trainer.start_recording(gesture_name, duration, progress_callback)
        
        # Recording happens in _process_loop via gesture mode
        # For now, use synchronous recording
        frames_recorded = 0
        start_time = time.time()
        
        temp_frames = []
        while time.time() - start_time < duration:
            ret, frame = self._capture.read()
            if not ret:
                continue
            
            _, landmarks = self.detector.detect(frame)
            if landmarks:
                temp_frames.append(landmarks)
                frames_recorded += 1
                
                if progress_callback:
                    progress = (time.time() - start_time) / duration
                    progress_callback(progress, frames_recorded)
            
            time.sleep(0.033)  # ~30fps
        
        # Create sample from recorded frames
        sample = GestureSample(
            name=gesture_name,
            frames=[
                GestureFrame(
                    timestamp=i * 0.033,
                    landmarks=landmarks,
                    frame_number=i
                )
                for i, landmarks in enumerate(temp_frames)
            ],
            duration=duration,
            metadata={'trained_at': time.time()}
        )
        
        if gesture_name not in self.trainer.gesture_samples:
            self.trainer.gesture_samples[gesture_name] = []
        self.trainer.gesture_samples[gesture_name].append(sample)
        
        logger.info(f"Trained gesture '{gesture_name}' with {len(temp_frames)} frames")
        return len(temp_frames) >= self.trainer.min_frames
    
    def list_gestures(self) -> List[str]:
        """List all trained gestures."""
        return self.trainer.list_gestures()
    
    def map_gesture(self, gesture_name: str, command: str) -> None:
        """Map a gesture to a command."""
        self.trainer.map_gesture_to_command(gesture_name, command)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            'is_running': self.is_running,
            'gestures_trained': len(self.trainer.list_gestures()),
            'gestures_mapped': len(self.trainer.gesture_mappings),
            'detector_available': MEDIAPIPE_AVAILABLE,
            'fps': sum(self.detector.fps_history) / len(self.detector.fps_history) if self.detector.fps_history else 0
        }


# Example usage and demonstration
def demo():
    """Demonstrate body controller functionality."""
    print("Chatty Commander Body Controller Demo")
    print("=" * 50)
    
    # Initialize
    controller = BodyController({
        'min_detection_confidence': 0.5,
        'min_tracking_confidence': 0.5
    })
    
    # Set callbacks
    def on_command(command: str):
        print(f"🎯 Executing command: {command}")
    
    def on_frame(frame):
        # In real app, display in GUI
        cv2.imshow("Body Controller", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            controller.stop()
    
    def on_detection(gesture: DetectedGesture):
        print(f"✋ Detected gesture: {gesture.name} ({gesture.confidence:.2f})")
    
    controller.set_command_callback(on_command)
    controller.set_frame_callback(on_frame)
    controller.set_detection_callback(on_detection)
    
    # Start
    if not controller.start(camera_index=0):
        print("Failed to start camera")
        return
    
    print("\nControls:")
    print("  't' - Train new gesture")
    print("  'm' - Map gesture to command")
    print("  'l' - List gestures")
    print("  'q' - Quit")
    print()
    
    try:
        while controller.is_running:
            key = cv2.waitKey(100) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('t'):
                name = input("Gesture name: ")
                controller.train_gesture(name, duration=2.0)
            elif key == ord('m'):
                gesture = input("Gesture name: ")
                command = input("Command: ")
                controller.map_gesture(gesture, command)
            elif key == ord('l'):
                gestures = controller.list_gestures()
                print(f"Trained gestures: {gestures}")
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        cv2.destroyAllWindows()
        print("\nDemo complete!")


if __name__ == "__main__":
    demo()
