# Gesture Control for Chatty Commander

Control Chatty Commander using body gestures and hand movements via OpenCV and MediaPipe.

## Overview

The gesture control system uses your webcam to detect body poses and recognize trained gestures, converting them into Chatty Commander commands.

**Features:**
- Real-time body wireframe detection (33 landmarks)
- Train custom gestures (2-second recordings)
- Pre-defined gesture templates
- Map gestures to any command
- Confidence-based recognition

## Installation

### Requirements

```bash
pip install opencv-python mediapipe numpy
```

### Verify Installation

```bash
python -c "import cv2; import mediapipe; print('✅ Dependencies ready')"
```

## Quick Start

### 1. Train Default Gestures

```bash
python -m chatty_commander.cli.gesture_trainer --setup-defaults
```

This trains 10 default gestures:
- `wave_right` → next_track
- `wave_left` → previous_track
- `thumbs_up` → volume_up
- `thumbs_down` → volume_down
- `point_up` → scroll_up
- `point_down` → scroll_down
- `clap` → play_pause
- `stop` → stop_all
- `ok_sign` → confirm
- `cross_arms` → mute

### 2. Enable in Chatty Commander

Add to your config:

```yaml
features:
  gesture: true
  
gesture:
  camera_index: 0
  setup_defaults: true
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
```

### 3. Start Chatty Commander

```bash
python -m chatty_commander
```

Stand in front of your camera and perform gestures!

## Training Custom Gestures

### Interactive Mode

```bash
python -m chatty_commander.cli.gesture_trainer
```

Follow the prompts to:
1. Select or name a gesture
2. Perform it for 2 seconds
3. Map it to a command

### Quick Train Specific Gestures

```bash
# Train multiple gestures in sequence
python -m chatty_commander.cli.gesture_trainer -t wave_right wave_left thumbs_up

# Train with specific camera
python -m chatty_commander.cli.gesture_trainer --camera 1 -t my_gesture
```

### Programmatic Training

```python
from chatty_commander.vision.gesture_adapter import create_gesture_adapter

# Create adapter
adapter = create_gesture_adapter({
    'camera_index': 0,
    'setup_defaults': False
})

# Start
adapter.start()

# Train
def on_progress(progress, frames):
    print(f"Recording... {int(progress*100)}%")

adapter.train_gesture('my_wave', duration=2.0)

# Map to command
adapter.map_gesture('my_wave', 'open_browser')
```

## Gesture Recognition

### How It Works

1. **Detection**: MediaPipe detects 33 body landmarks
2. **Tracking**: Key points (wrists, elbows, shoulders) are tracked
3. **Matching**: DTW-like algorithm compares to trained samples
4. **Confidence**: Match confidence must be ≥75%
5. **Cooldown**: 1-second cooldown between detections

### Recognition Pipeline

```
Camera Frame → Pose Detection → Landmark Extraction
                                    ↓
                              Gesture Buffer (30 frames)
                                    ↓
                              Similarity Matching
                                    ↓
                              Command Execution
```

## API Reference

### BodyController

Main controller class.

```python
from chatty_commander.vision.body_controller import BodyController

controller = BodyController(config)
controller.start(camera_index=0)

# Train
training_success = controller.train_gesture('wave', duration=2.0)

# Map
controller.map_gesture('wave', 'next_track')

# Status
status = controller.get_status()
# {'is_running': True, 'gestures_trained': 5, ...}
```

### GestureInputAdapter

Orchestrator integration.

```python
from chatty_commander.vision.gesture_adapter import GestureInputAdapter

adapter = GestureInputAdapter(config)
adapter.set_command_callback(lambda cmd: print(f"Execute: {cmd}"))
adapter.start()
```

### BodyWireframeDetector

Low-level pose detection.

```python
from chatty_commander.vision.body_controller import BodyWireframeDetector

detector = BodyWireframeDetector()
frame, landmarks = detector.detect(opencv_frame)

if landmarks:
    # 33 landmarks with x, y, z, visibility
    for i, lm in enumerate(landmarks):
        print(f"{detector.get_landmark_name(i)}: ({lm.x:.2f}, {lm.y:.2f})")
```

## Configuration

### Config Options

```yaml
gesture:
  # Camera
  camera_index: 0              # Which camera to use
  
  # Detection
  min_detection_confidence: 0.5   # Min confidence for pose detection
  min_tracking_confidence: 0.5    # Min confidence for landmark tracking
  model_complexity: 1           # 0=light, 1=full, 2=heavy
  enable_segmentation: false      # Enable person segmentation
  
  # Recognition
  similarity_threshold: 0.75    # Min confidence for gesture match
  cooldown_seconds: 1.0         # Seconds between detections
  
  # Training
  min_frames: 10                # Min frames for valid training
  max_frames: 60                # Max frames to store
  
  # Defaults
  setup_defaults: false         # Auto-train default gestures
  
  # Persistence
  gesture_config_path: ~/.chatty_commander/gestures.json
```

### Environment Variables

```bash
export GESTURE_CAMERA=0
export GESTURE_MIN_CONFIDENCE=0.5
export GESTURE_SETUP_DEFAULTS=true
```

## Default Gestures

| Gesture | Description | Default Command | Key Landmarks |
|---------|-------------|-----------------|---------------|
| wave_right | Wave right hand | next_track | right_wrist, right_elbow |
| wave_left | Wave left hand | previous_track | left_wrist, left_elbow |
| thumbs_up | Thumbs up | volume_up | right_thumb, right_wrist |
| thumbs_down | Thumbs down | volume_down | right_thumb, right_wrist |
| point_up | Point index up | scroll_up | right_index, right_wrist |
| point_down | Point index down | scroll_down | right_index, right_wrist |
| clap | Clap hands | play_pause | left_wrist, right_wrist |
| stop | Stop sign | stop_all | right_wrist, right_elbow, right_shoulder |
| ok_sign | OK sign | confirm | right_thumb, right_index |
| cross_arms | Cross arms | mute | left_wrist, right_wrist, shoulders |

## Troubleshooting

### Camera Not Found

```bash
# List available cameras
python -c "
import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera {i}: available')
        cap.release()
"

# Use camera 1 instead of 0
python -m chatty_commander --camera 1
```

### Poor Recognition

1. **Better lighting**: Ensure good, even lighting
2. **Clear background**: Plain background works best
3. **Full body visible**: Stand 6-8 feet from camera
4. **Retrain**: Train 3-5 samples of each gesture
5. **Adjust threshold**: Lower `similarity_threshold` to 0.6

### High CPU Usage

```yaml
gesture:
  model_complexity: 0      # Use light model
  min_detection_confidence: 0.3  # Lower threshold
```

### False Positives

```yaml
gesture:
  similarity_threshold: 0.85  # Require better match
  cooldown_seconds: 2.0       # Longer cooldown
```

## Performance

### Benchmarks

| Model | FPS @ 720p | CPU Usage | Accuracy |
|-------|-----------|-----------|----------|
| Light (0) | 30+ | Low | Good |
| Full (1) | 15-20 | Medium | Better |
| Heavy (2) | 10-15 | High | Best |

**Recommended**: Full (1) for most use cases

### Optimization Tips

1. Use lower camera resolution:
   ```python
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
   ```

2. Skip frames:
   ```python
   # Process every 2nd frame
   if frame_count % 2 == 0:
       detector.detect(frame)
   ```

3. Use GPU (if available):
   ```bash
   pip install mediapipe-silicon  # For Apple Silicon
   ```

## Advanced Usage

### Custom Gesture Classifier

```python
from chatty_commander.vision.body_controller import GestureRecognizer

recognizer = GestureRecognizer(trainer)

# Process frame
gesture = recognizer.process_frame(landmarks)

if gesture:
    print(f"Detected: {gesture.name} ({gesture.confidence:.2f})")
```

### Multiple Cameras

```python
# Front camera for gestures
front = BodyController({'camera_index': 0})

# Side camera for additional angles
side = BodyController({'camera_index': 1})

front.start()
side.start()
```

### Headless Mode

```python
# No GUI, just command execution
controller = BodyController(config)
controller.set_frame_callback(None)  # Don't display
controller.set_command_callback(execute_command)
controller.start()
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Chatty Commander Orchestrator          │
│  ┌─────────────────────────────────┐    │
│  │ GestureInputAdapter             │    │
│  │  ┌──────────────────────────┐  │    │
│  │  │ BodyController           │  │    │
│  │  │  ┌──────────────────┐    │  │    │
│  │  │  │ BodyWireframe    │    │  │    │
│  │  │  │ Detector         │    │  │    │
│  │  │  │  (MediaPipe)     │    │  │    │
│  │  │  └──────────────────┘    │  │    │
│  │  │         ↓                │  │    │
│  │  │  ┌──────────────────┐    │  │    │
│  │  │  │ Gesture          │    │  │    │
│  │  │  │ Recognizer       │    │  │    │
│  │  │  │  (DTW matching)  │    │  │    │
│  │  │  └──────────────────┘    │  │    │
│  │  └──────────────────────────┘  │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Security & Privacy

- All processing is local (no cloud)
- Camera feed never leaves your device
- Gesture data stored in `~/.chatty_commander/gestures.json`
- No images/videos are saved

## Contributing

To add new gesture templates:

1. Edit `GestureCommandMapper.DEFAULT_GESTURES`
2. Add landmark indices for key points
3. Document in this file
4. Submit PR

## License

MIT License - See LICENSE file

## Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Discord: [Chatty Commander Discord](https://discord.gg/example)
