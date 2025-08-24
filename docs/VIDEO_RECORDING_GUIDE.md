# 🎬 Video Recording Guide: Voice-Controlled Codex-CLI Demo

This guide helps you record the perfect demo video showing ChattyCommander's voice-controlled coding capabilities.

## 📋 Pre-Recording Setup

### 1. **Test Your Environment**
```bash
# Copy voice-only configuration
cp configs/voice-only-example.json config.json

# Test voice system
python3 src/chatty_commander/cli/cli.py voice status

# Run demo script to see the workflow
python3 scripts/voice_demo_recording.py
```

### 2. **Install Required Tools**
- **Codex-CLI**: Install and test it works
- **Screen Recorder**: OBS Studio, QuickTime, or similar
- **Audio Setup**: Test microphone quality and levels

### 3. **Configure Keybindings**
Test these keybindings work in your system:
- `Ctrl+Shift+V`: Start voice transcription
- `Ctrl+Shift+Enter`: Paste transcribed text and execute
- `Ctrl+Alt+C`: Trigger codex-cli (optional)

## 🎥 Recording Workflow

### **Scene Structure** (3 scenes, ~30 seconds each)

#### **Scene 1: Setup Introduction** (10 seconds)
- Show terminal with ChattyCommander
- Brief explanation: "Voice-controlled coding with ChattyCommander"
- Run: `python3 scripts/voice_demo_recording.py`

#### **Scene 2: Live Voice Demo** (60 seconds)
Record these 3 voice commands in sequence:

1. **Email Validation Function**
   - Say: "Hey coder, create a Python function that validates email addresses"
   - Show: Voice transcription → Codex response → Code in editor

2. **Fibonacci Function**
   - Say: "Create a function to calculate fibonacci numbers"
   - Show: Immediate code generation and pasting

3. **Dictionary Sorting**
   - Say: "Write a function to sort a list of dictionaries by a key"
   - Show: Complex request handled seamlessly

#### **Scene 3: Benefits Summary** (20 seconds)
- Quick montage showing:
  - No typing required
  - Instant code generation
  - Works with any editor
  - Offline processing

## 🔧 Technical Recording Tips

### **Audio Quality**
- Use a good microphone close to your mouth
- Record in a quiet environment
- Test audio levels before recording
- Speak clearly and at normal pace

### **Screen Recording**
- Record at 1920x1080 or higher
- Use 30fps minimum for smooth playback
- Include both screen and audio
- Show terminal, editor, and any relevant windows

### **Timing**
- Pause briefly between voice commands
- Allow time to show the generated code
- Keep total video under 2 minutes for engagement

## 📝 Sample Script

### **Opening** (10 seconds)
> "Here's ChattyCommander transforming coding with voice control. Watch me generate Python functions using only voice commands—no typing required."

### **Demo Commands** (speak naturally)
1. "Hey coder, create a Python function that validates email addresses"
2. "Create a function to calculate fibonacci numbers"  
3. "Write a function to sort a list of dictionaries by a key"

### **Closing** (10 seconds)
> "Three functions generated in under a minute, hands-free. Voice-controlled coding with ChattyCommander—describe what you want, get working code instantly."

## 🎬 Video Structure

```
[0:00-0:10] Introduction & Setup
[0:10-0:30] Voice Command 1: Email Validation
[0:30-0:50] Voice Command 2: Fibonacci Function  
[0:50-1:10] Voice Command 3: Dictionary Sorting
[1:10-1:30] Benefits & Call to Action
```

## 📋 Recording Checklist

**Before Recording:**
- [ ] Voice-only config copied and tested
- [ ] Codex-cli installed and working
- [ ] Microphone tested and positioned
- [ ] Screen recorder configured
- [ ] Demo script rehearsed
- [ ] Background noise minimized

**During Recording:**
- [ ] Speak clearly and at natural pace
- [ ] Pause between commands for processing
- [ ] Show the generated code clearly
- [ ] Demonstrate the workflow smoothly

**After Recording:**
- [ ] Review audio quality
- [ ] Check all code generation is visible
- [ ] Verify timing and pacing
- [ ] Add captions if needed

## 🎯 Success Criteria

**Great demo video should show:**
- ✅ Clear voice commands being spoken
- ✅ Instant transcription and processing
- ✅ High-quality code generation
- ✅ Seamless workflow integration
- ✅ No manual typing or interruption
- ✅ Professional presentation

## 📤 Post-Recording

### **Video Editing**
- Add title cards for each scene
- Include captions for accessibility  
- Add brief text overlays explaining each step
- Export in multiple formats (MP4, GIF)

### **Documentation Update**
Replace the video placeholder in `docs/CONFIGURATION_EXAMPLES.md`:

```markdown
**🎬 Voice-Controlled Codex-CLI Demo**
[![Voice Coding Demo](thumbnail.png)](your-video-url)
*Click to watch: Voice commands → Code generation in under 2 minutes*
```

### **Sharing**
- Upload to YouTube/Vimeo with good title and description
- Create animated GIF for quick previews
- Share on social media with relevant hashtags
- Add to project README and documentation

---

**Ready to record?** Run the demo script first to practice, then start recording! 🎬