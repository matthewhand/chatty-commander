# ChattyCommander Troubleshooting Guide

## Common Issues and Solutions

### 1. Models Not Loading
- **Symptoms**: Error messages about missing models or ONNX files.
- **Solutions**:
  - Ensure ONNX files are in correct directories: models-idle/, models-computer/, models-chatty/.
  - Check file permissions.
  - Verify paths in config.json.
  - Run `uv run python main.py --debug` for detailed logs.

### 2. Audio Detection Problems
- **Symptoms**: No response to voice commands, microphone not detecting input.
- **Solutions**:
  - Check microphone permissions in OS settings.
  - Test microphone with `uv run python test_audio.py` (if available).
  - Adjust sample rate in config.json (default: 16000).
  - Reduce background noise.

### 3. Command Execution Failures
- **Symptoms**: Command detected but action not performed.
- **Solutions**:
  - Verify model_actions in config.json match detected commands.
  - For URL commands, check network connectivity and endpoint.
  - For keypress, ensure pyautogui is installed and no focus issues.
  - Review logs in logs/chattycommander.log.

### 4. State Transition Issues
- **Symptoms**: Stuck in one state, not switching on wake words.
- **Solutions**:
  - Confirm wake words are correctly mapped in config.
  - Test with CLI simulation: `uv run chatty shell` and type commands.
  - Reload models: Restart the application.

### 5. Performance Problems
- **Symptoms**: High latency or CPU usage.
- **Solutions**:
  - Optimize models with openwakeword tools.
  - Reduce number of active models.
  - Run on hardware with better specs.

### 6. Web/GUI Specific Issues
- **Symptoms**: Interface not loading or WebSocket disconnects.
- **Solutions**:
  - Check browser console for errors.
  - Ensure correct ports are open (default: 8100 for web).
  - Clear browser cache.

## Advanced Debugging
- Enable verbose logging in config.json.
- Use `pdb` for breakpoints in code.
- Check system resources with `top` or `htop`.

If issues persist, check GitHub issues or create a new one with log excerpts.