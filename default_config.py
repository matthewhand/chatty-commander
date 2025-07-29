#!/usr/bin/env python3
"""
Default Configuration Generator for ChattyCommander

This module creates a default configuration when no configuration is detected,
including sample wakeword files and proper directory structure with symlinks.
"""

import os
import json
import logging
from pathlib import Path

class DefaultConfigGenerator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.wakewords_dir = self.base_dir / "wakewords"
        self.config_file = self.base_dir / "config.json"
        
        # Default wakeword files (these would be actual .onnx files in practice)
        self.default_wakewords = {
            "hey_chat_tee.onnx": "idle",  # Transition to chatty mode
            "hey_khum_puter.onnx": "idle",  # Transition to computer mode
            "okay_stop.onnx": "all",  # Available in all modes
            "oh_kay_screenshot.onnx": "computer",  # Computer-specific command
            "lights_on.onnx": "idle",  # Home automation
            "lights_off.onnx": "idle",  # Home automation
            "wax_poetic.onnx": "chatty",  # Chatty-specific command
            "thanks_chat_tee.onnx": "chatty",  # Chatty exit command
            "that_ill_do.onnx": "chatty",  # Chatty exit command
        }
        
    def generate_default_config(self):
        """Generate a complete default configuration."""
        logging.info("Generating default configuration...")
        
        # Create wakewords directory if it doesn't exist
        self.wakewords_dir.mkdir(exist_ok=True)
        
        # Create sample wakeword files (placeholders)
        self._create_sample_wakewords()
        
        # Create model directories and symlinks
        self._setup_model_directories()
        
        # Generate default config.json
        self._create_default_config_json()
        
        logging.info("Default configuration created successfully!")
        
    def _create_sample_wakewords(self):
        """Create sample wakeword files in the wakewords directory."""
        for wakeword_file in self.default_wakewords.keys():
            wakeword_path = self.wakewords_dir / wakeword_file
            if not wakeword_path.exists():
                # Create a placeholder file (in practice, these would be actual ONNX models)
                with open(wakeword_path, 'w') as f:
                    f.write(f"# Placeholder for {wakeword_file}\n")
                    f.write("# This should be replaced with an actual ONNX model file\n")
                logging.info(f"Created placeholder wakeword file: {wakeword_file}")
                
    def _setup_model_directories(self):
        """Create model directories and set up symlinks to wakeword files."""
        model_dirs = {
            "models-idle": ["hey_chat_tee.onnx", "hey_khum_puter.onnx", "okay_stop.onnx", "lights_on.onnx", "lights_off.onnx"],
            "models-computer": ["oh_kay_screenshot.onnx", "okay_stop.onnx"],
            "models-chatty": ["wax_poetic.onnx", "thanks_chat_tee.onnx", "that_ill_do.onnx", "okay_stop.onnx"]
        }
        
        for model_dir, wakewords in model_dirs.items():
            dir_path = self.base_dir / model_dir
            dir_path.mkdir(exist_ok=True)
            
            for wakeword in wakewords:
                source = self.wakewords_dir / wakeword
                target = dir_path / wakeword
                
                # Remove existing symlink if it exists
                if target.is_symlink() or target.exists():
                    target.unlink()
                    
                # Create symlink
                try:
                    target.symlink_to(source.resolve())
                    logging.info(f"Created symlink: {target} -> {source}")
                except OSError as e:
                    logging.warning(f"Could not create symlink {target}: {e}")
                    # Fallback: copy the file instead
                    import shutil
                    shutil.copy2(source, target)
                    logging.info(f"Copied file instead: {source} -> {target}")
                    
    def _create_default_config_json(self):
        """Create a comprehensive default config.json file."""
        default_config = {
            "keybindings": {
                "take_screenshot": "alt+print_screen",
                "paste": "ctrl+v",
                "cycle_window": "alt+tab",
                "open_run": "win+r",
                "start_typing": "ctrl+shift+;",
                "stop_typing": "ctrl+shift+;",
                "submit": "enter"
            },
            "commands": {
                "take_screenshot": {
                    "action": "keypress",
                    "keys": "take_screenshot"
                },
                "paste": {
                    "action": "keypress",
                    "keys": "paste"
                },
                "submit": {
                    "action": "keypress",
                    "keys": "submit"
                },
                "cycle_window": {
                    "action": "keypress",
                    "keys": "cycle_window"
                },
                "okay_send": {
                    "action": "keypress",
                    "keys": "submit"
                },
                "okay_stop": {
                    "action": "keypress",
                    "keys": "stop_typing"
                },
                "oh_kay_screenshot": {
                    "action": "keypress",
                    "keys": "take_screenshot"
                },
                "thanks_chat_tee": {
                    "action": "custom_message",
                    "message": "That'll do, bro"
                },
                "that_ill_do": {
                    "action": "custom_message",
                    "message": "Thanks chatty, dude"
                },
                "lights_on": {
                    "action": "url",
                    "url": "{home_assistant}/lights_on"
                },
                "lights_off": {
                    "action": "url",
                    "url": "{home_assistant}/lights_off"
                },
                "wax_poetic": {
                    "action": "url",
                    "url": "{chatbot_endpoint}"
                }
            },
            "command_sequences": {
                "screenshot_paste_submit": [
                    {
                        "command": "take_screenshot",
                        "delay_after_ms": 3000
                    },
                    {
                        "command": "paste",
                        "delay_after_ms": 1000
                    },
                    {
                        "command": "submit",
                        "delay_after_ms": 0
                    }
                ]
            },
            "api_endpoints": {
                "home_assistant": "http://homeassistant.domain.home:8123/api",
                "chatbot_endpoint": "http://localhost:3100/"
            },
            "state_models": {
                "idle": ["hey_chat_tee", "hey_khum_puter", "okay_stop", "lights_on", "lights_off"],
                "computer": ["oh_kay_screenshot", "okay_stop"],
                "chatty": ["wax_poetic", "thanks_chat_tee", "that_ill_do", "okay_stop"]
            },
            "model_paths": {
                "idle": "models-idle",
                "computer": "models-computer",
                "chatty": "models-chatty"
            },
            "audio_settings": {
                "mic_chunk_size": 1024,
                "sample_rate": 16000,
                "audio_format": "int16"
            },
            "general_settings": {
                "debug_mode": True,
                "default_state": "idle",
                "inference_framework": "onnx",
                "start_on_boot": false,
                "check_for_updates": true
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        logging.info(f"Created default config.json at {self.config_file}")
        
    def should_generate_default_config(self):
        """Check if default configuration should be generated."""
        # Check if config.json exists and is valid
        if not self.config_file.exists():
            return True
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Check if essential sections exist
                required_sections = ['commands', 'state_models']
                if not all(section in config for section in required_sections):
                    return True
        except (json.JSONDecodeError, IOError):
            return True
            
        # Check if model directories are empty
        model_dirs = ['models-idle', 'models-computer', 'models-chatty']
        all_empty = True
        for model_dir in model_dirs:
            dir_path = self.base_dir / model_dir
            if dir_path.exists() and any(dir_path.iterdir()):
                all_empty = False
                break
                
        return all_empty
        
def generate_default_config_if_needed():
    """Generate default configuration if needed."""
    generator = DefaultConfigGenerator()
    if generator.should_generate_default_config():
        logging.info("No valid configuration detected. Generating default configuration...")
        generator.generate_default_config()
        return True
    return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_default_config_if_needed()