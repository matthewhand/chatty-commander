# Body Animation Controls - Technical Deep Dive

## Overview

Transform full-body animations and movements into precise control inputs for Chatty Commander using computer vision and skeletal tracking.

## Architecture

```
Camera Feed
     ↓
┌─────────────────────────────────────────┐
│  BodyWireframeDetector (MediaPipe)      │
│  - 33 3D landmarks                      │
│  - Real-time tracking (30fps)           │
│  - Confidence scoring                   │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│  Gesture Recognizer                   │
│  - Skeletal pattern matching          │
│  - Dynamic Time Warping (DTW)         │
│  - Confidence threshold (75%)         │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│  Command Mapper                       │
│  - Gesture → Command translation      │
│  - Context-aware routing              │
│  - Multi-modal fusion                 │
└─────────────────────────────────────────┘
     ↓
Chatty Commander Execution
```

## Body Animation Types

### 1. **Discrete Gestures** (Binary Triggers)

Single-frame recognizable poses that trigger commands.

| Gesture | Landmarks | Trigger Condition |
|---------|-----------|-------------------|
| **Thumbs Up** | Thumb tip above IP joint | `thumb_tip.y < thumb_ip.y` |
| **Stop Hand** | Palm facing camera, fingers extended | `wrist.z < finger_tips.z` |
| **Point** | Index extended, others curled | `index_tip.dist(wrist) > others.dist(wrist)` |
| **Fist** | All fingertips near palm | `Σ finger_tip.dist(wrist) < threshold` |
| **Peace Sign** | Index+middle extended, ring+pinky curled | Boolean combination |
| **OK Sign** | Thumb+index touching | `thumb_tip.dist(index_tip) < ε` |

**Implementation:**
```python
def detect_thumbs_up(landmarks):
    wrist = landmarks[0]  # WRIST
    thumb_tip = landmarks[4]    # THUMB_TIP
    thumb_ip = landmarks[3]     # THUMB_IP
    
    # Check thumb is above knuckle
    return thumb_tip.y < thumb_ip.y and thumb_tip.y < wrist.y
```

### 2. **Continuous Animations** (Analog Controls)

Ongoing movements that map to continuous values (like mouse position, volume).

| Animation | Control Type | Mapping |
|-----------|--------------|---------|
| **Hand Position** | 2D Cursor | (x, y) → Screen coordinates |
| **Arm Extension** | Slider (0-1) | Elbow angle → Value |
| **Body Lean** | Balance control | Hip center offset → Left/Right |
| **Arm Circle** | Rotary knob | Angular velocity → Value change |
| **Head Tilt** | Scroll control | Neck angle → Scroll speed |

**Implementation:**
```python
def hand_to_cursor(landmarks, screen_width, screen_height):
    # Use dominant hand (e.g., right)
    wrist = landmarks[16]  # RIGHT_WRIST
    
    # Map normalized [0,1] to screen pixels
    x = int(wrist.x * screen_width)
    y = int(wrist.y * screen_height)
    
    # Smooth with exponential moving average
    smoothed_x = 0.8 * prev_x + 0.2 * x
    smoothed_y = 0.8 * prev_y + 0.2 * y
    
    return (smoothed_x, smoothed_y)
```

### 3. **Sequential Animations** (Command Sequences)

Time-series movements that require specific motion patterns.

| Sequence | Description | Recognition |
|----------|-------------|-------------|
| **Wave Right** | 3+ oscillations right hand | FFT peak detection |
| **Clap** | Hands meet then separate | Distance minimum detection |
| **Circle** | Circular arm motion | Angular momentum tracking |
| **Swipe** | Linear hand movement | Velocity vector consistency |
| **March** | Alternating leg lifts | Periodic signal detection |

**Implementation:**
```python
class SequenceRecognizer:
    def detect_wave(self, history_buffer):
        # Extract right wrist x-coordinate over time
        wrist_x = [frame.landmarks[16].x for frame in history_buffer]
        
        # Apply FFT to find dominant frequency
        fft = np.fft.fft(wrist_x)
        freqs = np.fft.fftfreq(len(wrist_x))
        
        # Wave is 2-4 Hz oscillation
        dominant_freq = freqs[np.argmax(np.abs(fft))]
        return 2 < abs(dominant_freq) * 30 < 4  # Assuming 30fps
```

### 4. **Compound Animations** (Multi-Point Gestures)

Coordinated multi-limb movements for complex commands.

| Compound | Components | Logic |
|----------|------------|-------|
| **Cross Arms** | Both wrists near opposite shoulders | `left_wrist.near(right_shoulder) AND right_wrist.near(left_shoulder)` |
| **T-Pose** | Arms horizontal, legs together | `elbows.y ≈ shoulders.y AND wrists.y ≈ shoulders.y` |
| **Jump** | Hips rise then fall | `hip_y.max - hip_y.min > threshold` |
| **Squat** | Hips lower, knees bend | `hip_y > normal_hip_y AND knee_angle < 90°` |
| **Spin** | Body rotation | `shoulder_center.x` oscillation |

## Technical Implementation Details

### Landmark Indices (MediaPipe 33-point)

```
0: NOSE
1-2: LEFT/RIGHT EYE (inner)
3-4: LEFT/RIGHT EYE
5-6: LEFT/RIGHT EYE (outer)
7-8: LEFT/RIGHT EAR
9-10: LEFT/RIGHT MOUTH
11-12: LEFT/RIGHT SHOULDER
13-14: LEFT/RIGHT ELBOW
15-16: LEFT/RIGHT WRIST
17-18: LEFT/RIGHT PINKY
19-20: LEFT/RIGHT INDEX
21-22: LEFT/RIGHT THUMB
23-24: LEFT/RIGHT HIP
25-26: LEFT/RIGHT KNEE
27-28: LEFT/RIGHT ANKLE
29-30: LEFT/RIGHT HEEL
31-32: LEFT/RIGHT FOOT_INDEX
```

### Coordinate System

```
Normalized [0.0, 1.0]:
  x: Left (0) → Right (1)
  y: Top (0) → Bottom (1)
  z: Near (0) → Far (1), relative to hip

Visibility: 0.0 (occluded) → 1.0 (fully visible)
```

### Confidence Thresholding

```python
MIN_VISIBILITY = 0.5  # Landmark must be 50%+ visible
MIN_DETECTION_CONF = 0.5  # Overall pose confidence

if landmark.visibility < MIN_VISIBILITY:
    landmark = None  # Treat as unknown
```

### Temporal Smoothing

```python
class TemporalSmoother:
    """Exponential moving average for jitter reduction."""
    
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.history = {}
    
    def smooth(self, landmark_id, value):
        if landmark_id not in self.history:
            self.history[landmark_id] = value
            return value
        
        smoothed = self.alpha * value + (1 - self.alpha) * self.history[landmark_id]
        self.history[landmark_id] = smoothed
        return smoothed
```

## Animation Training Pipeline

### Step 1: Recording

```python
# Capture 2-3 seconds of movement
recording = []
for frame in capture_frames(duration=2.0, fps=30):
    landmarks = detector.detect(frame)
    if landmarks:
        recording.append({
            'timestamp': frame.time,
            'landmarks': landmarks,
            'visibility': avg_visibility(landmarks)
        })
```

### Step 2: Feature Extraction

```python
def extract_features(recording):
    """Convert raw landmarks to control features."""
    features = []
    
    for frame in recording:
        lm = frame['landmarks']
        
        # Extract relevant features
        feature_vector = {
            # Hand positions (normalized)
            'right_hand_x': lm[16].x,
            'right_hand_y': lm[16].y,
            'left_hand_x': lm[15].x,
            'left_hand_y': lm[15].y,
            
            # Arm angles
            'right_arm_angle': angle(lm[12], lm[14], lm[16]),
            'left_arm_angle': angle(lm[11], lm[13], lm[15]),
            
            # Body pose
            'torso_rotation': (lm[11].x + lm[12].x) / 2 - (lm[23].x + lm[24].x) / 2,
            
            # Relative distances
            'hands_distance': distance(lm[15], lm[16]),
        }
        
        features.append(feature_vector)
    
    return features
```

### Step 3: Template Storage

```python
gesture_template = {
    'name': 'wave_right',
    'type': 'sequential',
    'features': features,  # Time-series
    'key_landmarks': [16, 14, 12],  # Right arm chain
    'duration_range': (1.5, 3.0),  # Acceptable duration
    'tolerance': 0.2,  # Matching tolerance
}
```

### Step 4: Real-time Matching

```python
def match_gesture(live_buffer, templates):
    """Find best matching template."""
    best_score = 0
    best_match = None
    
    live_features = extract_features(live_buffer)
    
    for template in templates:
        score = dtw_distance(live_features, template['features'])
        
        if score > best_score and score > template['tolerance']:
            best_score = score
            best_match = template
    
    return best_match, best_score
```

## Control Categories

### Media Controls

```python
MEDIA_GESTURES = {
    'play_pause': 'clap',
    'next_track': 'swipe_right',
    'previous_track': 'swipe_left',
    'volume_up': 'thumbs_up_held',
    'volume_down': 'thumbs_down_held',
    'mute': 'cross_arms',
}
```

### Navigation Controls

```python
NAV_GESTURES = {
    'scroll_up': 'point_up',
    'scroll_down': 'point_down',
    'click': 'pinch',
    'right_click': 'two_finger_tap',
    'drag': 'fist_held',
    'zoom_in': 'spread_apart',
    'zoom_out': 'pinch_together',
}
```

### System Controls

```python
SYSTEM_GESTURES = {
    'screenshot': 'ok_sign',
    'lock_screen': 'stop_hold_3s',
    'switch_app': 'wave_left',
    'close_app': 'wave_right',
    'emergency_stop': 'both_arms_up',
}
```

### Custom Macros

```python
MACRO_GESTURES = {
    'dev_mode': 'konami_code_with_body',  # Secret sequence
    'present_mode': 't_pose_hold',
    'focus_mode': 'hands_together',
    'break_reminder': 'stand_up_detected',
}
```

## Advanced Features

### 1. Context Awareness

```python
class ContextAwareController:
    def __init__(self):
        self.current_app = None
        self.user_state = 'idle'
    
    def route_gesture(self, gesture):
        # Different meanings in different contexts
        if self.current_app == 'browser':
            if gesture == 'swipe_left':
                return 'browser_back'
        elif self.current_app == 'video_player':
            if gesture == 'swipe_left':
                return 'seek_backward'
        
        return gesture.default_command
```

### 2. Multi-Modal Fusion

```python
def combine_inputs(voice_cmd, gesture, eye_tracking):
    """Fuse multiple input modalities."""
    
    # Voice is primary
    if voice_cmd.confidence > 0.9:
        return voice_cmd
    
    # Gesture confirms voice
    if gesture.matches(voice_cmd):
        return voice_cmd  # Confirmed
    
    # Disagreement - use eye tracking to disambiguate
    if eye_tracking.looking_at('confirmation_button'):
        return voice_cmd
    
    return None  # Unclear, ask again
```

### 3. Adaptive Thresholds

```python
class AdaptiveRecognizer:
    def __init__(self):
        self.user_accuracy_history = []
    
    def adjust_threshold(self):
        """Make recognition stricter if user makes errors."""
        recent_accuracy = np.mean(self.user_accuracy_history[-10:])
        
        if recent_accuracy < 0.7:
            self.confidence_threshold += 0.05  # Stricter
        elif recent_accuracy > 0.95:
            self.confidence_threshold -= 0.02  # More lenient
```

### 4. Fatigue Detection

```python
def detect_fatigue(landmarks_history):
    """Detect when user is getting tired."""
    
    # Check for reduced movement range
    recent_range = max(l.y for l in landmarks_history[-30:]) - \
                   min(l.y for l in landmarks_history[-30:])
    
    baseline_range = max(l.y for l in landmarks_history[:30]) - \
                     min(l.y for l in landmarks_history[:30])
    
    if recent_range < baseline_range * 0.5:
        return True  # User is fatigued
    
    return False
```

## Performance Optimization

### Frame Skipping

```python
class OptimizedDetector:
    def __init__(self, target_fps=30, inference_fps=10):
        self.skip_ratio = target_fps // inference_fps
        self.frame_count = 0
    
    def should_process(self):
        self.frame_count += 1
        return self.frame_count % self.skip_ratio == 0
```

### Region of Interest

```python
def crop_to_user(frame, landmarks):
    """Crop frame to user bounding box to reduce processing."""
    if not landmarks:
        return frame
    
    xs = [l.x for l in landmarks if l.visibility > 0.5]
    ys = [l.y for l in landmarks if l.visibility > 0.5]
    
    if not xs or not ys:
        return frame
    
    # Add padding
    padding = 0.1
    x_min = max(0, min(xs) - padding)
    x_max = min(1, max(xs) + padding)
    y_min = max(0, min(ys) - padding)
    y_max = min(1, max(ys) + padding)
    
    h, w = frame.shape[:2]
    return frame[int(y_min*h):int(y_max*h), int(x_min*w):int(x_max*w)]
```

## Future Enhancements

### 1. Machine Learning Classifier

Replace DTW with trained neural network:
```python
# Train LSTM on gesture sequences
model = Sequential([
    LSTM(64, input_shape=(30, 10)),  # 30 frames, 10 features
    Dense(32, activation='relu'),
    Dense(len(gesture_classes), activation='softmax')
])
```

### 2. Haptic Feedback

```python
def provide_feedback(gesture_detected):
    """Vibrate phone/watch when gesture recognized."""
    if gesture_detected.confidence > 0.9:
        haptic.strong_tap()
    elif gesture_detected.confidence > 0.7:
        haptic.light_tap()
```

### 3. Augmented Reality Overlay

```python
def draw_ar_feedback(frame, landmarks, target_gesture):
    """Show user what gesture to perform."""
    
    # Draw ghost outline of target gesture
    ghost = get_target_ghost(target_gesture)
    overlay = blend_frames(frame, ghost, alpha=0.3)
    
    # Color current pose based on match quality
    match_quality = compute_match(landmarks, ghost)
    color = (0, 255, 0) if match_quality > 0.8 else (0, 165, 255) if match_quality > 0.5 else (0, 0, 255)
    
    draw_landmarks(overlay, landmarks, color)
    return overlay
```

## Summary

Body animation controls enable:
- **Hands-free operation** - No keyboard/mouse needed
- **Accessibility** - Users with mobility limitations
- **Speed** - Gestures faster than typing for common actions
- **Intuitiveness** - Natural mappings (thumbs up = good/confirm)
- **Hygiene** - No touching shared surfaces
- **Future-ready** - Foundation for VR/AR integration

The key is the 33-point skeletal model providing rich spatial data that can be mapped to virtually any control paradigm through intelligent feature extraction and temporal analysis.
