# Voice Command Training Guide

## Overview

ChattyCommander uses ONNX models for voice recognition, powered by the openwakeword library. This guide explains how to train custom models for new voice commands.

## Prerequisites

- Python 3.11+
- openwakeword library (install via `uv add openwakeword`)
- Audio dataset for your command (positive and negative samples)

## Steps to Train a Custom Model

1. **Prepare Dataset**:
   - Collect positive audio clips saying your command.
   - Gather negative clips (background noise, other speech).
   - Organize in directories: positives/ and negatives/.

2. **Train the Model**:
   Use openwakeword's training script:

   ```python
   import openwakeword
   oww = openwakeword.Model()
   oww.train(positive_dir='positives/', negative_dir='negatives/', output_model='custom_command.onnx')
   ```

   Note: This is a simplified example. Refer to openwakeword docs for full parameters.

3. **Export to ONNX**:
   Ensure the model is exported in ONNX format.

4. **Integrate with ChattyCommander**:
   - Place the .onnx file in the appropriate directory (e.g., models-idle/ for idle state).
   - Update config.json to map the model to an action.
     Example:

   ```json
   "model_actions": {
     "custom_command": {"keypress": "ctrl+alt+t"}
   }
   ```

5. **Test the Model**:
   Run the app and test your new command.

## Best Practices

- Use at least 100 positive and 1000 negative samples.
- Train in a quiet environment.
- Fine-tune thresholds in config.

For advanced training, see openwakeword documentation: https://github.com/dscripka/openWakeWord
