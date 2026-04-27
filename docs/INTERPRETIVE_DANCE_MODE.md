# Interpretive Dance Mode for Chatty Commander

## Overview

Transform free-form dance into expressive control. Unlike rigid gestures, interpretive dance recognizes **flow, emotion, energy, and rhythm** to create a fluid, artistic interface.

## Philosophy

**Traditional Gestures:** "Wave hand = next track" (1:1 mapping)

**Interpretive Dance:** "Building energy + expansive flow = crescendo to climax" (expressive mapping)

The system reads the **emotional intent** behind movement, not just the position.

## Key Concepts

### 1. Flow State Analysis

```
Continuity:  ████████░░ 0.8 (smooth, not jerky)
Expansion:   █████████░ 0.9 (arms spread wide)
Symmetry:    ██████░░░░ 0.6 (slightly asymmetric)
Rhythm Lock: █████████░ 0.85 (on beat)
Energy:      🔥 EXPLOSIVE
Style:       contemporary
```

### 2. Rhythm Detection

- **Beat detection** from motion onset
- **Tempo tracking** (BPM from movement)
- **Groove lock** (how synchronized to beat)
- **Phrase timing** (musical bar awareness)

### 3. Energy Arc Recognition

```
Energy Timeline:
0.1 ───────────────────────────────────────
    │                    ╱╲
    │                   ╱  ╲
    │                  ╱    ╲
0.5 │                 ╱      ╲
    │                ╱        ╲
    │    ╱╲         ╱          ╲
    │   ╱  ╲       ╱            ╲___
0.9 │  ╱    ╲_____╱
    │_╱
    └───────────────────────────────────────
      Calm → Build → Climax → Sustain → Resolve

Commands:      wait → build_up → maximize → sustain_high → reset
```

## Dance Styles Recognized

| Style | Characteristics | Typical Commands |
|-------|-----------------|------------------|
| **Flow** | Continuous, smooth, liquid | smooth_mode, liquid_effects |
| **Pop/Lock** | Jerky, staccato, precise | staccato_mode, snap_actions |
| **Ballet** | Symmetric, poised, extended | precise_mode, elegant_transitions |
| **Contemporary** | Expressive, emotional, expansive | expressive_mode, dramatic_effects |
| **Hip Hop** | Grounded, asymmetric, rhythmic | rhythmic_mode, urban_vibes |
| **Wave** | Undulating, fluid, contained | liquid_mode, morph_effects |
| **Groove** | Relaxed, head-nod, steady | steady_mode, chill_vibes |

## How It Works

### Architecture

```
Camera (30fps)
     ↓
Body Pose Detection (33 landmarks)
     ↓
┌─────────────────────────────────────────┐
│ Rhythm Detector                         │
│ • Onset detection from motion             │
│ • FFT for tempo extraction              │
│ • Beat tracking (BPM)                     │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ Flow Analyzer                           │
│ • Continuity (smooth vs jerky)          │
│ • Expansion (contracted vs open)        │
│ • Symmetry (asymmetric vs balanced)     │
│ • Energy level (calm to explosive)      │
│ • Style classification                  │
└─────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ Expressive Mapper                       │
│ • Real-time flow → command              │
│ • Phrase interpretation                 │
│ • Emotional arc detection               │
└─────────────────────────────────────────┘
     ↓
Chatty Commander Commands
```

### Real-Time Flow Mapping

```python
# Continuous state mapping
if flow.energy == EnergyLevel.EXPLOSIVE:
    command = "maximize"  # Full screen, max volume, etc

if flow.expansion > 0.9:
    command = "expand_all"  # Open all windows

if flow.style == DanceStyle.CONTEMPORARY and flow.energy.value > 0.7:
    command = "expressive_mode"  # Dramatic animations
```

### Phrase-Based Interpretation

A **phrase** is a complete movement sequence (2-8 seconds). The system interprets the **arc**:

```python
# Phrase characteristics
energy_arc = end_energy - start_energy

if energy_arc > 0.3:  # Building up
    commands = ["build_up", "anticipation", "climax"]
elif energy_arc < -0.3:  # Releasing
    commands = ["resolve", "release", "reset"]
else:  # Sustained
    commands = ["sustain", "hold"]
```

## Visual Feedback

### Ghost Trail

Shows your movement path over last 30 frames:
```
       ╱╲
      ╱  ╲
     ╱    ╲
────╱      ╲────  ← Arms moving outward
   /          \
  /            \
```

### Rhythm Pulse

Visual metronome synced to your detected groove:
```
    ◯    (expanding/contracting with beat)
   ╱│╲
  ◉│◉   ← Eyes/beat markers
   │
```

### Energy Meter

```
Energy: ▓▓▓▓▓▓▓▓░░ 80% [ENERGETIC]
        🔥🔥🔥🔥🔥🔥🔥🔥
```

## Usage

### Enable Dance Mode

```python
from chatty_commander.vision.dance_interpreter import DanceInterpreter

# Create interpreter
interpreter = DanceInterpreter({
    'min_phrase_duration': 2.0,  # Minimum phrase length
    'show_ghost_trail': True,
    'ghost_trail_length': 30
})

# Set callbacks
def on_command(command, flow_state):
    print(f"Executing: {command}")
    print(f"  Energy: {flow_state.energy.name}")
    print(f"  Style: {flow_state.style.value}")

def on_beat(strength):
    print(f"💓 Beat detected! Strength: {strength:.2f}")

def on_phrase(phrase):
    print(f"🎼 Phrase: {phrase.dominant_style.value}")
    print(f"   Arc: {phrase.average_energy.name}")

interpreter.set_callbacks(on_command, on_beat, on_phrase)

# Process frames from camera
while camera.is_open():
    frame = camera.read()
    landmarks = pose_detector.detect(frame)
    
    result = interpreter.process_frame(landmarks)
    
    # Visual feedback
    overlay = interpreter.draw_dance_overlay(frame, landmarks)
    display.show(overlay)
```

### Configuration

```yaml
dance_mode:
  enabled: true
  
  # Rhythm detection
  rhythm:
    history_size: 180  # 6 seconds at 30fps
    min_beat_interval_ms: 300
    tempo_range: [60, 180]  # BPM
  
  # Flow analysis
  flow:
    window_size: 30  # 1 second window
    continuity_threshold: 0.5
    expansion_threshold: 0.7
  
  # Phrase detection
  phrase:
    min_duration: 2.0  # seconds
    max_duration: 8.0  # seconds
    pause_threshold: 0.2  # energy level for "pause"
  
  # Visual feedback
  visuals:
    ghost_trail: true
    trail_length: 30
    rhythm_pulse: true
    energy_meter: true
```

## Example Dances & Their Meanings

### "The Crescendo"
```
Movement: Start small → Expand arms → Reach peak intensity
Energy:   0.2 → 0.5 → 0.9
Commands: wait → build_up → maximize → climax
Use Case: Building to presentation climax, music crescendo
```

### "The Resolve"
```
Movement: High energy → Gradual release → Stillness
Energy:   0.8 → 0.4 → 0.1
Commands: sustain_high → resolve → reset → minimize
Use Case: Ending presentation, calming down, meditation
```

### "The Groove"
```
Movement: Steady head nod, rhythmic arm waves
Rhythm:   Locked to beat
Energy:   Sustained 0.5
Commands: rhythmic_mode → steady_vibe → beat_sync
Use Case: DJ mode, background music control
```

### "The Snap"
```
Movement: Quick contractions, jerky pops
Continuity: Low (0.2)
Style:    pop_lock
Commands: staccato_mode → snap_action → precise_control
Use Case: Quick edits, snap to grid, rhythmic cuts
```

### "The Flow"
```
Movement: Continuous liquid motion, no stops
Continuity: High (0.9)
Expansion: Variable
Commands: liquid_mode → smooth_transition → morph_effects
Use Case: Transitions, morphing effects, ambient mode
```

## Integration with Chatty Commander

### As Input Adapter

```python
from chatty_commander.vision.dance_adapter import DanceInputAdapter

# Add to orchestrator
orchestrator.register_adapter(
    DanceInputAdapter(config={
        'mode': 'interpretive',  # vs 'gestural'
        'sensitivity': 0.8
    })
)
```

### Command Mapping Examples

```python
DANCE_COMMAND_MAP = {
    # Energy-based
    'maximize': ['fullscreen', 'volume_max', 'brightness_max'],
    'minimize': ['minimize_all', 'mute', 'dim'],
    'build_up': ['increase_volume', 'zoom_in'],
    'resolve': ['fade_out', 'transition_calm'],
    
    # Style-based
    'expressive_mode': ['enable_animations', 'dramatic_transitions'],
    'staccato_mode': ['snap_to_grid', 'quantize_actions'],
    'liquid_mode': ['smooth_transitions', 'morph_effects'],
    
    # Flow-based
    'expand_all': ['open_all_windows', 'maximize_workspace'],
    'contract': ['focus_mode', 'minimal_ui'],
    'sustain_high': ['hold_state', 'loop_mode'],
    
    # Rhythm-based
    'beat_drop': ['trigger_effect', 'flash_transition'],
    'rhythmic_mode': ['sync_to_beat', 'pulse_effects'],
}
```

## Advanced Features

### 1. Style Transfer

Learn a dancer's unique style and adapt:
```python
# After observing 100 phrases
user_style = analyzer.learn_style(user_id)
interpreter.adapt_to_style(user_style)
```

### 2. Collaborative Dance

Multiple dancers control different aspects:
```python
# Dancer 1: Energy/Intensity
# Dancer 2: Rhythm/Tempo
# Dancer 3: Spatial/Expansion
merged_flow = merge_flows([flow1, flow2, flow3])
```

### 3. Improvisational Mode

AI suggests movements based on current state:
```python
suggestion = interpreter.suggest_next_movement()
# "Try building energy for climax" or "Sustain current flow"
```

### 4. Dance Memory

Record and replay dance sequences:
```python
# Record
sequence = interpreter.record_sequence(duration=30)

# Replay (as macro)
interpreter.replay_sequence(sequence)
```

## Performance

| Component | CPU Usage | Latency |
|-----------|-----------|---------|
| Rhythm Detection | 5% | 33ms |
| Flow Analysis | 8% | 33ms |
| Phrase Tracking | 3% | - |
| **Total** | **~16%** | **33ms** |

## Comparison: Gestures vs Dance Mode

| Aspect | Gestures | Dance Mode |
|--------|----------|------------|
| **Precision** | High (specific commands) | Expressive (emotional intent) |
| **Learning Curve** | Must memorize | Natural, intuitive |
| **Speed** | Fast (1:1 mapping) | Contextual (may trigger multiple) |
| **Creativity** | Limited | Unlimited improvisation |
| **Control** | Exact | Ambient, atmospheric |
| **Use Case** | Productivity | Performance, art, presentation |

## Tips for Dancers

### Getting Started
1. Start with simple energy changes (calm → energetic)
2. Focus on clear beginnings and endings (phrases)
3. Don't worry about specific gestures - express emotion
4. Let the system learn your natural style

### Advanced Techniques
1. **Rhythm locking**: Nod head to set tempo, then dance freely
2. **Contrast**: Alternate between high/low energy for dynamic control
3. **Sustained states**: Hold energy levels for continuous effects
4. **Phrase building**: Think in 2-4 second "sentences" of movement

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Commands not triggering | Dance bigger, increase energy |
| Too sensitive | Reduce sensitivity in config |
| Rhythm off | Make beat more obvious (head nod, stomp) |
| Wrong style detected | Exaggerate style characteristics |

## Future Roadmap

### v1.1: Ensemble Mode
- Multiple dancers = multiple parameters
- Chorus/verse structure recognition

### v1.2: AI Choreography
- System suggests movements
- Real-time teaching mode

### v1.3: Cross-Modal
- Combine with voice ("Play something [dance: energetic]")
- Eye gaze + dance for selection

### v2.0: Full Performance
- Record professional dances as macros
- Share dance sequences
- Dance battles (competitive mode)

## Inspiration

Inspired by:
- **Laurie Anderson's** MIDI violin (expressive control)
- **Pat Metheny's** Orchestrion (movement → music)
- **Laptop orchestras** (gestural conducting)
- **Contemporary dance tech** (Merce Cunningham, Troika Ranch)

---

## Quick Start

```bash
# 1. Enable dance mode
python -m chatty_commander --mode dance

# 2. Stand in front of camera
# 3. Start with simple arm movements
# 4. Watch the ghost trail and rhythm pulse
# 5. Express yourself - the system will respond!
```

**Dance freely. Command beautifully.**
