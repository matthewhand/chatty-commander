"""
Interpretive Dance Mode for Chatty Commander.

Transforms free-form dance movements into expressive control inputs.
Recognizes flow, rhythm, energy, and emotional intent from body motion.
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import time
from scipy.signal import spectrogram
from scipy.fft import fft


class DanceStyle(Enum):
    """Recognized dance styles/modes."""
    FREE_FORM = "free_form"
    BALLET = "ballet"
    HIP_HOP = "hip_hop"
    CONTEMPORARY = "contemporary"
    WAVE = "wave"
    POP_LOCK = "pop_lock"
    FLOW = "flow"
    GROOVE = "groove"


class EnergyLevel(Enum):
    """Detected energy/emotional intensity."""
    MEDITATIVE = 0.1
    CALM = 0.3
    GROOVING = 0.5
    ENERGETIC = 0.7
    INTENSE = 0.9
    EXPLOSIVE = 1.0


@dataclass
class MotionVector:
    """3D motion vector with temporal data."""
    x: float
    y: float
    z: float
    velocity: float
    acceleration: float
    timestamp: float


@dataclass
class FlowState:
    """Current flow characteristics of dancer."""
    continuity: float  # 0-1, smooth vs jerky
    expansion: float  # 0-1, contracted vs expansive
    symmetry: float   # 0-1, asymmetric vs symmetric
    rhythm_lock: float  # 0-1, off-beat vs on-beat
    energy: EnergyLevel
    style: DanceStyle


@dataclass
class DancePhrase:
    """A complete movement phrase with intent."""
    start_time: float
    end_time: float
    movements: List[MotionVector]
    flow_states: List[FlowState]
    dominant_style: DanceStyle
    average_energy: EnergyLevel
    intent: str  # Interpreted emotional/command intent
    commands_triggered: List[str] = field(default_factory=list)


class RhythmDetector:
    """
    Detect beat, tempo, and rhythm from motion patterns.
    
    Uses FFT on motion magnitude to find dominant frequencies.
    """
    
    def __init__(self, history_size: int = 180):  # 6 seconds at 30fps
        self.motion_history = deque(maxlen=history_size)
        self.beat_times = deque(maxlen=16)
        self.tempo_bpm = 0
        self.last_beat_time = 0
        self.beat_confidence = 0.0
        
    def add_frame(self, landmarks: List[Any]) -> Optional[float]:
        """
        Process frame and detect beats.
        
        Returns:
            Beat strength if beat detected, None otherwise
        """
        if not landmarks:
            return None
        
        # Calculate total body motion
        total_motion = self._calculate_motion_magnitude(landmarks)
        timestamp = time.time()
        
        self.motion_history.append({
            'timestamp': timestamp,
            'magnitude': total_motion
        })
        
        # Need enough history
        if len(self.motion_history) < 60:  # 2 seconds
            return None
        
        # Detect beat using onset detection
        beat_strength = self._detect_onset(total_motion)
        
        if beat_strength > 0.7:  # Strong beat
            time_since_last = timestamp - self.last_beat_time
            
            # Minimum 300ms between beats (prevent double detection)
            if time_since_last > 0.3:
                self.beat_times.append(timestamp)
                self.last_beat_time = timestamp
                
                # Update tempo from recent beats
                if len(self.beat_times) >= 4:
                    self._update_tempo()
                
                return beat_strength
        
        return None
    
    def _calculate_motion_magnitude(self, landmarks: List[Any]) -> float:
        """Calculate total body motion magnitude."""
        # Use hips as center of mass reference
        if len(landmarks) < 25:
            return 0.0
        
        hip_center = np.array([
            (landmarks[23].x + landmarks[24].x) / 2,
            (landmarks[23].y + landmarks[24].y) / 2,
            (landmarks[23].z + landmarks[24].z) / 2
        ])
        
        # Calculate weighted motion of extremities
        weights = {
            15: 1.0, 16: 1.0,  # Wrists
            19: 0.8, 20: 0.8,  # Index fingers
            27: 0.6, 28: 0.6,  # Ankles
        }
        
        total_motion = 0.0
        for idx, weight in weights.items():
            if idx < len(landmarks):
                pos = np.array([landmarks[idx].x, landmarks[idx].y, landmarks[idx].z])
                velocity = np.linalg.norm(pos - hip_center)
                total_motion += velocity * weight
        
        return total_motion
    
    def _detect_onset(self, current_magnitude: float) -> float:
        """Detect rhythmic onset/beat using local energy function."""
        if len(self.motion_history) < 10:
            return 0.0
        
        # Get recent history
        recent = list(self.motion_history)[-10:]
        magnitudes = [h['magnitude'] for h in recent]
        
        # Local energy
        local_energy = np.mean([m**2 for m in magnitudes])
        instant_energy = current_magnitude ** 2
        
        # Onset detection: instant energy vs local average
        if local_energy > 0:
            onset_ratio = instant_energy / (local_energy + 1e-10)
            
            # Peak detection in onset
            if onset_ratio > 1.5 and current_magnitude > np.mean(magnitudes):
                return min(1.0, (onset_ratio - 1.5) / 2.0)
        
        return 0.0
    
    def _update_tempo(self):
        """Calculate tempo from beat intervals."""
        if len(self.beat_times) < 2:
            return
        
        intervals = []
        beats = list(self.beat_times)
        for i in range(1, len(beats)):
            intervals.append(beats[i] - beats[i-1])
        
        if intervals:
            avg_interval = np.median(intervals)
            if avg_interval > 0:
                self.tempo_bpm = int(60.0 / avg_interval)
                # Confidence based on interval consistency
                self.beat_confidence = 1.0 - (np.std(intervals) / avg_interval)
    
    def get_tempo(self) -> Tuple[int, float]:
        """Get detected tempo and confidence."""
        return self.tempo_bpm, self.beat_confidence
    
    def is_on_beat(self, tolerance_ms: float = 100) -> bool:
        """Check if current time is on a beat."""
        if not self.beat_times or self.tempo_bpm == 0:
            return False
        
        time_since_last = time.time() - self.last_beat_time
        beat_duration = 60.0 / self.tempo_bpm
        
        # Check if we're close to expected next beat
        phase = time_since_last % beat_duration
        return phase < (tolerance_ms / 1000.0) or phase > (beat_duration - tolerance_ms / 1000.0)


class FlowAnalyzer:
    """
    Analyze flow characteristics of movement.
    
    Detects continuity, expansion, symmetry - key elements of dance quality.
    """
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.position_history = deque(maxlen=window_size)
        self.velocity_history = deque(maxlen=window_size)
        
    def analyze_frame(self, landmarks: List[Any]) -> FlowState:
        """Analyze current flow state from landmarks."""
        if not landmarks or len(landmarks) < 25:
            return FlowState(
                continuity=0.5,
                expansion=0.5,
                symmetry=0.5,
                rhythm_lock=0.0,
                energy=EnergyLevel.CALM,
                style=DanceStyle.FREE_FORM
            )
        
        # Extract key points
        left_wrist = np.array([landmarks[15].x, landmarks[15].y, landmarks[15].z])
        right_wrist = np.array([landmarks[16].x, landmarks[16].y, landmarks[16].z])
        left_shoulder = np.array([landmarks[11].x, landmarks[11].y, landmarks[11].z])
        right_shoulder = np.array([landmarks[12].x, landmarks[12].y, landmarks[12].z])
        hip_center = np.array([
            (landmarks[23].x + landmarks[24].x) / 2,
            (landmarks[23].y + landmarks[24].y) / 2,
            (landmarks[23].z + landmarks[24].z) / 2
        ])
        
        # Calculate velocities
        current_pos = np.array([left_wrist, right_wrist, hip_center])
        timestamp = time.time()
        
        if self.position_history:
            last_pos, last_time = self.position_history[-1]
            dt = timestamp - last_time
            if dt > 0:
                velocity = (current_pos - last_pos) / dt
                self.velocity_history.append(velocity)
        
        self.position_history.append((current_pos, timestamp))
        
        # Calculate flow metrics
        continuity = self._calculate_continuity()
        expansion = self._calculate_expansion(landmarks)
        symmetry = self._calculate_symmetry(left_wrist, right_wrist, left_shoulder, right_shoulder)
        energy = self._calculate_energy()
        style = self._detect_style(continuity, expansion, symmetry, energy)
        
        return FlowState(
            continuity=continuity,
            expansion=expansion,
            symmetry=symmetry,
            rhythm_lock=0.5,  # Would need rhythm detector integration
            energy=energy,
            style=style
        )
    
    def _calculate_continuity(self) -> float:
        """Calculate motion continuity (smoothness)."""
        if len(self.velocity_history) < 3:
            return 0.5
        
        # Jerk = change in acceleration
        velocities = list(self.velocity_history)
        accelerations = []
        for i in range(1, len(velocities)):
            acc = np.linalg.norm(velocities[i] - velocities[i-1])
            accelerations.append(acc)
        
        if len(accelerations) < 2:
            return 0.5
        
        jerks = []
        for i in range(1, len(accelerations)):
            jerk = abs(accelerations[i] - accelerations[i-1])
            jerks.append(jerk)
        
        avg_jerk = np.mean(jerks) if jerks else 0
        # Lower jerk = higher continuity
        continuity = 1.0 - min(1.0, avg_jerk / 10.0)
        return continuity
    
    def _calculate_expansion(self, landmarks: List[Any]) -> float:
        """Calculate body expansion vs contraction."""
        # Measure how spread out limbs are
        hip = np.array([
            (landmarks[23].x + landmarks[24].x) / 2,
            (landmarks[23].y + landmarks[24].y) / 2
        ])
        
        extremities = [15, 16, 27, 28]  # Wrists and ankles
        distances = []
        
        for idx in extremities:
            if idx < len(landmarks):
                pos = np.array([landmarks[idx].x, landmarks[idx].y])
                dist = np.linalg.norm(pos - hip)
                distances.append(dist)
        
        if not distances:
            return 0.5
        
        # Normalize by typical body scale (shoulder width)
        shoulder_width = abs(landmarks[11].x - landmarks[12].x) if len(landmarks) > 12 else 0.1
        if shoulder_width > 0:
            avg_expansion = np.mean(distances) / shoulder_width
            return min(1.0, avg_expansion / 3.0)  # Normalize to 0-1
        
        return 0.5
    
    def _calculate_symmetry(self, left_wrist, right_wrist, left_shoulder, right_shoulder) -> float:
        """Calculate body symmetry."""
        # Compare left vs right side positions
        shoulder_mid = (left_shoulder + right_shoulder) / 2
        
        left_relative = left_wrist - shoulder_mid
        right_relative = right_wrist - shoulder_mid
        
        # Mirror right to compare
        right_mirrored = np.array([-right_relative[0], right_relative[1], right_relative[2]])
        
        # Calculate symmetry as inverse of difference
        diff = np.linalg.norm(left_relative - right_mirrored)
        symmetry = 1.0 - min(1.0, diff / 2.0)
        
        return symmetry
    
    def _calculate_energy(self) -> EnergyLevel:
        """Calculate energy level from motion."""
        if not self.velocity_history:
            return EnergyLevel.CALM
        
        # Average velocity magnitude
        recent_velocities = list(self.velocity_history)[-10:]
        avg_velocity = np.mean([np.linalg.norm(v) for v in recent_velocities])
        
        # Map to energy levels
        if avg_velocity < 0.1:
            return EnergyLevel.MEDITATIVE
        elif avg_velocity < 0.3:
            return EnergyLevel.CALM
        elif avg_velocity < 0.6:
            return EnergyLevel.GROOVING
        elif avg_velocity < 1.0:
            return EnergyLevel.ENERGETIC
        elif avg_velocity < 1.5:
            return EnergyLevel.INTENSE
        else:
            return EnergyLevel.EXPLOSIVE
    
    def _detect_style(self, continuity: float, expansion: float, symmetry: float, energy: EnergyLevel) -> DanceStyle:
        """Detect dance style from flow characteristics."""
        # Style detection heuristics
        if continuity > 0.8 and expansion > 0.6:
            return DanceStyle.FLOW
        elif continuity < 0.3 and energy.value >= 0.7:
            return DanceStyle.POP_LOCK
        elif symmetry > 0.8 and continuity > 0.6:
            return DanceStyle.BALLET
        elif expansion > 0.7 and energy.value >= 0.5:
            return DanceStyle.CONTEMPORARY
        elif continuity < 0.5 and symmetry < 0.4:
            return DanceStyle.HIP_HOP
        elif continuity > 0.7 and expansion < 0.3:
            return DanceStyle.WAVE
        elif energy.value >= 0.5 and continuity > 0.4:
            return DanceStyle.GROOVE
        else:
            return DanceStyle.FREE_FORM


class ExpressiveCommandMapper:
    """
    Maps expressive dance qualities to commands.
    
    Unlike literal gesture mapping, this uses:
    - Energy level for intensity
    - Flow state for mode
    - Rhythm for timing
    - Style for context
    """
    
    def __init__(self):
        self.command_intensity = 0.0
        self.active_mode = "neutral"
        self.last_phrase_end = 0
        
    def map_flow_to_command(self, flow: FlowState, on_beat: bool = False) -> Optional[str]:
        """
        Map current flow state to command.
        
        Returns command if triggered, None otherwise.
        """
        commands = []
        
        # Energy-based commands
        if flow.energy == EnergyLevel.EXPLOSIVE:
            commands.append("maximize")
        elif flow.energy == EnergyLevel.INTENSE:
            commands.append("boost")
        elif flow.energy == EnergyLevel.MEDITATIVE:
            commands.append("minimize")
        
        # Style-based context switching
        if flow.style == DanceStyle.BALLET:
            self.active_mode = "precise"
        elif flow.style == DanceStyle.HIP_HOP:
            self.active_mode = "rhythmic"
        elif flow.style == DanceStyle.FLOW:
            self.active_mode = "smooth"
        
        # Expansion-based commands
        if flow.expansion > 0.9:
            commands.append("expand_all")
        elif flow.expansion < 0.1:
            commands.append("contract")
        
        # Symmetry-based commands
        if flow.symmetry > 0.95:
            commands.append("balance")
        elif flow.symmetry < 0.2:
            commands.append("asymmetric_mode")
        
        # Beat-synced commands
        if on_beat and flow.rhythm_lock > 0.7:
            if flow.energy.value >= 0.7:
                commands.append("beat_drop")
        
        return commands if commands else None
    
    def interpret_phrase(self, phrase: DancePhrase) -> List[str]:
        """
        Interpret a complete dance phrase into commands.
        
        This is where the "interpretive" magic happens -
        understanding the emotional arc of a movement sequence.
        """
        commands = []
        
        # Analyze phrase arc
        energies = [fs.energy.value for fs in phrase.flow_states]
        energy_arc = energies[-1] - energies[0]  # Build vs release
        
        # Building energy = crescendo action
        if energy_arc > 0.3:
            commands.append("build_up")
            if phrase.average_energy.value >= 0.7:
                commands.append("climax")
        
        # Releasing energy = resolution
        elif energy_arc < -0.3:
            commands.append("resolve")
            if phrase.average_energy.value <= 0.3:
                commands.append("reset")
        
        # Sustained energy = holding state
        elif np.std(energies) < 0.1:
            if phrase.average_energy.value >= 0.6:
                commands.append("sustain_high")
            else:
                commands.append("sustain_low")
        
        # Style-specific interpretations
        if phrase.dominant_style == DanceStyle.CONTEMPORARY:
            commands.append("expressive_mode")
        elif phrase.dominant_style == DanceStyle.POP_LOCK:
            commands.append("staccato_mode")
        elif phrase.dominant_style == DanceStyle.WAVE:
            commands.append("liquid_mode")
        
        return commands


class DanceInterpreter:
    """
    Main interpretive dance controller.
    
    Combines rhythm detection, flow analysis, and expressive mapping
to create a fluid, artistic control interface.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Sub-analyzers
        self.rhythm_detector = RhythmDetector()
        self.flow_analyzer = FlowAnalyzer()
        self.command_mapper = ExpressiveCommandMapper()
        
        # Phrase tracking
        self.current_phrase_start = time.time()
        self.phrase_movements: List[MotionVector] = []
        self.phrase_flows: List[FlowState] = []
        self.min_phrase_duration = 2.0  # Minimum seconds for a phrase
        
        # State
        self.is_recording = False
        self.on_command: Optional[Callable[[str, FlowState], None]] = None
        self.on_beat: Optional[Callable[[float], None]] = None
        self.on_phrase_complete: Optional[Callable[[DancePhrase], None]] = None
        
        # Visual feedback
        self.show_ghost_trail = True
        self.ghost_trail_length = 30
        self.position_trail = deque(maxlen=self.ghost_trail_length)
        
    def set_callbacks(
        self,
        on_command: Optional[Callable[[str, FlowState], None]] = None,
        on_beat: Optional[Callable[[float], None]] = None,
        on_phrase: Optional[Callable[[DancePhrase], None]] = None
    ):
        """Set event callbacks."""
        self.on_command = on_command
        self.on_beat = on_beat
        self.on_phrase_complete = on_phrase
    
    def process_frame(self, landmarks: List[Any]) -> Dict[str, Any]:
        """
        Process a frame of dance movement.
        
        Returns:
            Dict with current state and any triggered commands.
        """
        result = {
            'commands': [],
            'flow_state': None,
            'on_beat': False,
            'tempo': 0,
            'phrase_active': False
        }
        
        if not landmarks:
            return result
        
        # Update rhythm detection
        beat_strength = self.rhythm_detector.add_frame(landmarks)
        if beat_strength and self.on_beat:
            self.on_beat(beat_strength)
            result['on_beat'] = True
        
        # Update flow analysis
        flow = self.flow_analyzer.analyze_frame(landmarks)
        result['flow_state'] = flow
        
        # Track position for ghost trail
        if len(landmarks) > 16:
            self.position_trail.append({
                'left_wrist': (landmarks[15].x, landmarks[15].y),
                'right_wrist': (landmarks[16].x, landmarks[16].y),
                'timestamp': time.time()
            })
        
        # Map to commands
        on_beat = result['on_beat']
        commands = self.command_mapper.map_flow_to_command(flow, on_beat)
        
        if commands:
            result['commands'].extend(commands)
            if self.on_command:
                for cmd in commands:
                    self.on_command(cmd, flow)
        
        # Track phrase
        self._update_phrase(landmarks, flow)
        result['phrase_active'] = len(self.phrase_movements) > 0
        result['tempo'] = self.rhythm_detector.tempo_bpm
        
        return result
    
    def _update_phrase(self, landmarks: List[Any], flow: FlowState):
        """Update current phrase tracking."""
        now = time.time()
        phrase_duration = now - self.current_phrase_start
        
        # Add to current phrase
        self.phrase_flows.append(flow)
        
        # Calculate motion vector
        # (Simplified - would need actual position tracking)
        motion = MotionVector(
            x=0, y=0, z=0,
            velocity=0.1,
            acceleration=0.01,
            timestamp=now
        )
        self.phrase_movements.append(motion)
        
        # Check for phrase completion
        # Phrase ends when: significant pause, style change, or max duration
        if phrase_duration >= self.min_phrase_duration:
            if len(self.phrase_flows) > 10:
                # Check for pause (low energy)
                recent_energy = self.phrase_flows[-1].energy.value
                if recent_energy < 0.2:
                    self._complete_phrase()
                # Or max duration
                elif phrase_duration > 8.0:
                    self._complete_phrase()
    
    def _complete_phrase(self):
        """Complete current phrase and interpret."""
        now = time.time()
        
        if len(self.phrase_flows) < 5:
            # Too short, reset
            self._reset_phrase()
            return
        
        # Calculate phrase characteristics
        avg_energy = np.mean([f.energy.value for f in self.phrase_flows])
        dominant_style = max(set(self.phrase_flows), key=lambda x: self.phrase_flows.count(x)).style
        
        phrase = DancePhrase(
            start_time=self.current_phrase_start,
            end_time=now,
            movements=self.phrase_movements.copy(),
            flow_states=self.phrase_flows.copy(),
            dominant_style=dominant_style,
            average_energy=EnergyLevel(avg_energy),
            intent="expressive"
        )
        
        # Interpret phrase
        commands = self.command_mapper.interpret_phrase(phrase)
        phrase.commands_triggered = commands
        
        if commands and self.on_command:
            for cmd in commands:
                self.on_command(cmd, phrase.flow_states[-1])
        
        if self.on_phrase_complete:
            self.on_phrase_complete(phrase)
        
        # Reset for next phrase
        self._reset_phrase()
    
    def _reset_phrase(self):
        """Reset phrase tracking."""
        self.current_phrase_start = time.time()
        self.phrase_movements.clear()
        self.phrase_flows.clear()
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualizing dance state."""
        return {
            'ghost_trail': list(self.position_trail),
            'tempo': self.rhythm_detector.tempo_bpm,
            'beat_confidence': self.rhythm_detector.beat_confidence,
            'is_on_beat': self.rhythm_detector.is_on_beat(),
            'trail_length': len(self.position_trail)
        }
    
    def draw_dance_overlay(self, frame: np.ndarray, landmarks: List[Any]) -> np.ndarray:
        """
        Draw interpretive dance visualization overlay.
        
        Shows:
        - Ghost trail of movement
        - Rhythm pulse visualization
        - Energy level indicator
        - Flow state
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw ghost trail
        if len(self.position_trail) > 1:
            for i in range(1, len(self.position_trail)):
                alpha = i / len(self.position_trail)
                prev = self.position_trail[i-1]
                curr = self.position_trail[i]
                
                # Left wrist trail
                p1 = (int(prev['left_wrist'][0] * w), int(prev['left_wrist'][1] * h))
                p2 = (int(curr['left_wrist'][0] * w), int(curr['left_wrist'][1] * h))
                color = (int(255 * (1-alpha)), int(255 * alpha), 128)
                cv2.line(overlay, p1, p2, color, 2)
                
                # Right wrist trail
                p1 = (int(prev['right_wrist'][0] * w), int(prev['right_wrist'][1] * h))
                p2 = (int(curr['right_wrist'][0] * w), int(curr['right_wrist'][1] * h))
                cv2.line(overlay, p1, p2, color, 2)
        
        # Draw rhythm pulse circle
        tempo, confidence = self.rhythm_detector.get_tempo()
        if tempo > 0:
            center = (w - 100, 100)
            max_radius = 50
            
            # Pulsing based on beat proximity
            time_since_beat = time.time() - self.rhythm_detector.last_beat_time
            beat_duration = 60.0 / tempo if tempo > 0 else 1.0
            phase = (time_since_beat % beat_duration) / beat_duration
            
            radius = int(max_radius * (1 - phase) * confidence)
            color = (0, int(255 * confidence), int(255 * (1-confidence)))
            cv2.circle(overlay, center, radius, color, 3)
            
            # Tempo text
            cv2.putText(overlay, f"{tempo} BPM", (center[0]-30, center[1]+60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return overlay


# Example usage and demo
def demo_interpretive_dance():
    """Demonstrate interpretive dance mode."""
    print("Interpretive Dance Mode Demo")
    print("=" * 50)
    
    interpreter = DanceInterpreter()
    
    def on_command(cmd, flow):
        print(f"🎭 {cmd.upper()} | Energy: {flow.energy.name}, Style: {flow.style.value}")
    
    def on_beat(strength):
        print(f"💓 Beat! (strength: {strength:.2f})")
    
    def on_phrase(phrase):
        print(f"🎼 Phrase complete: {phrase.dominant_style.value}")
        print(f"   Commands: {phrase.commands_triggered}")
    
    interpreter.set_callbacks(on_command, on_beat, on_phrase)
    
    print("\nDance freely! The system will interpret your movements.")
    print("Commands:")
    print("  EXPLOSIVE energy → maximize")
    print("  SUSTAINED flow → sustain_high/sustain_low")
    print("  BUILDING phrase → build_up, climax")
    print("  RELEASING phrase → resolve, reset")
    print("  CONTEMPORARY style → expressive_mode")
    print()
    
    # Simulated dance frames would go here
    print("(Simulating dance input...)")
    
    # Mock data
    from dataclasses import dataclass
    
    @dataclass
    class MockLandmark:
        x: float
        y: float
        z: float = 0.0
    
    # Simulate building energy
    for i in range(60):  # 2 seconds at 30fps
        # Increasing motion magnitude
        magnitude = 0.1 + (i / 60) * 1.5
        
        # Create expanding movement
        landmarks = [
            MockLandmark(0.5, 0.5),  # Hip
            MockLandmark(0.5 - magnitude * 0.1, 0.5 - magnitude * 0.1),  # Left wrist
            MockLandmark(0.5 + magnitude * 0.1, 0.5 - magnitude * 0.1),  # Right wrist
        ] + [MockLandmark(0.5, 0.5)] * 30  # Fill rest
        
        result = interpreter.process_frame(landmarks)
        
        if result['commands']:
            print(f"Frame {i}: {result['commands']}")
    
    print("\nDemo complete!")


if __name__ == "__main__":
    demo_interpretive_dance()
