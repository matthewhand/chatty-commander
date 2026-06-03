# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive tests for default configuration generator module.

Tests configuration generation, wakeword file creation, directory setup, and validation.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.chatty_commander.app.default_config import (
    DefaultConfigGenerator,
    generate_default_config_if_needed,
)


class TestDefaultConfigGenerator:
    """Test DefaultConfigGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create DefaultConfigGenerator instance with temp directory."""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            gen = DefaultConfigGenerator()
            return gen

    def test_generator_initialization(self, generator, temp_dir):
        """Test DefaultConfigGenerator initialization."""
        assert generator.base_dir == temp_dir
        assert generator.wakewords_dir == temp_dir / "wakewords"
        assert generator.config_file == temp_dir / "config.json"

    def test_default_wakewords_defined(self, generator):
        """Test that default wakewords are properly defined."""
        assert hasattr(generator, "default_wakewords")
        assert isinstance(generator.default_wakewords, dict)
        assert len(generator.default_wakewords) > 0

        # Check expected wakewords
        expected_wakewords = [
            "hey_chat_tee.onnx",
            "hey_khum_puter.onnx",
            "okay_stop.onnx",
            "oh_kay_screenshot.onnx",
        ]

        for wakeword in expected_wakewords:
            assert wakeword in generator.default_wakewords

    def test_generate_default_config_creates_wakewords_dir(self, generator, temp_dir):
        """Test that config generation creates wakewords directory."""
        generator.generate_default_config()

        assert generator.wakewords_dir.exists()
        assert generator.wakewords_dir.is_dir()

    def test_create_sample_wakewords(self, generator, temp_dir):
        """Test creation of sample wakeword files."""
        generator.wakewords_dir.mkdir(exist_ok=True)
        generator._create_sample_wakewords()

        # Check that placeholder files were created
        for wakeword_file in generator.default_wakewords.keys():
            wakeword_path = generator.wakewords_dir / wakeword_file
            assert wakeword_path.exists()
            assert wakeword_path.is_file()

            # Check content
            with open(wakeword_path) as f:
                content = f.read()
                assert "Placeholder" in content
                assert wakeword_file in content

    def test_setup_model_directories(self, generator, temp_dir):
        """Test setup of model directories and symlinks."""
        # First create wakewords
        generator.wakewords_dir.mkdir(exist_ok=True)
        generator._create_sample_wakewords()

        # Setup model directories
        generator._setup_model_directories()

        # Check directories were created
        model_dirs = ["models-idle", "models-computer", "models-chatty"]
        for model_dir in model_dirs:
            dir_path = temp_dir / model_dir
            assert dir_path.exists()
            assert dir_path.is_dir()

    def test_create_default_config_json(self, generator, temp_dir):
        """Test creation of default config.json."""
        generator._create_default_config_json()

        assert generator.config_file.exists()
        assert generator.config_file.is_file()

        # Validate JSON content
        with open(generator.config_file) as f:
            config = json.load(f)

        # Check essential sections
        required_sections = ["commands", "state_models", "keybindings"]
        for section in required_sections:
            assert section in config

    def test_config_json_content_structure(self, generator, temp_dir):
        """Test structure of generated config.json."""
        generator._create_default_config_json()

        with open(generator.config_file) as f:
            config = json.load(f)

        # Check commands section
        assert "commands" in config
        assert isinstance(config["commands"], dict)
        assert len(config["commands"]) > 0

        # Check state_models section
        assert "state_models" in config
        assert isinstance(config["state_models"], dict)

        # Check keybindings section
        assert "keybindings" in config
        assert isinstance(config["keybindings"], dict)

        # Check audio_settings
        assert "audio_settings" in config
        assert "mic_chunk_size" in config["audio_settings"]
        assert "sample_rate" in config["audio_settings"]

        # Check logging section
        assert "logging" in config
        assert "level" in config["logging"]

    def test_should_generate_default_config_no_config(self, generator, temp_dir):
        """Test should_generate_default_config when no config exists."""
        # Ensure no config file exists
        if generator.config_file.exists():
            generator.config_file.unlink()

        result = generator.should_generate_default_config()
        assert result is True

    def test_should_generate_default_config_existing_valid_config(
        self, generator, temp_dir
    ):
        """Test should_generate_default_config with existing valid config."""
        # Create a valid config file
        generator._create_default_config_json()

        # Create model directories with content
        model_dir = temp_dir / "models-idle"
        model_dir.mkdir(exist_ok=True)
        (model_dir / "test_model.onnx").touch()

        result = generator.should_generate_default_config()
        assert result is False

    def test_should_generate_default_config_invalid_json(self, generator, temp_dir):
        """Test should_generate_default_config with invalid JSON."""
        # Create invalid config file
        with open(generator.config_file, "w") as f:
            f.write("invalid json{")

        result = generator.should_generate_default_config()
        assert result is True

    def test_should_generate_default_config_missing_sections(self, generator, temp_dir):
        """Test should_generate_default_config with missing required sections."""
        # Create config with missing sections
        incomplete_config = {"keybindings": {}}
        with open(generator.config_file, "w") as f:
            json.dump(incomplete_config, f)

        result = generator.should_generate_default_config()
        assert result is True

    def test_should_generate_all_empty_model_dirs(self, generator, temp_dir):
        """Test should_generate_default_config when all model dirs are empty."""
        # Create valid config
        generator._create_default_config_json()

        # Create empty model directories
        for model_dir in ["models-idle", "models-computer", "models-chatty"]:
            (temp_dir / model_dir).mkdir(exist_ok=True)

        result = generator.should_generate_default_config()
        assert result is True


class TestGenerateDefaultConfigIfNeeded:
    """Test generate_default_config_if_needed function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_generate_when_needed(self, temp_dir):
        """Test generation when config is needed."""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.chatty_commander.app.default_config.DefaultConfigGenerator"
            ) as MockGen:
                mock_instance = MockGen.return_value
                mock_instance.should_generate_default_config.return_value = True

                result = generate_default_config_if_needed()

                assert result is True
                mock_instance.generate_default_config.assert_called_once()

    def test_no_generation_when_not_needed(self, temp_dir):
        """Test no generation when config exists."""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.chatty_commander.app.default_config.DefaultConfigGenerator"
            ) as MockGen:
                mock_instance = MockGen.return_value
                mock_instance.should_generate_default_config.return_value = False

                result = generate_default_config_if_needed()

                assert result is False
                mock_instance.generate_default_config.assert_not_called()


class TestDefaultConfigIntegration:
    """Integration tests for default configuration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = Path.cwd()
            try:
                os.chdir(tmp_dir)
                yield Path(tmp_dir)
            finally:
                os.chdir(original_cwd)

    def test_full_config_generation_flow(self, temp_dir):
        """Test complete config generation flow."""
        generator = DefaultConfigGenerator()

        # Generate config
        generator.generate_default_config()

        # Verify wakewords directory and files
        assert generator.wakewords_dir.exists()
        for wakeword_file in generator.default_wakewords.keys():
            assert (generator.wakewords_dir / wakeword_file).exists()

        # Verify model directories
        for model_dir in ["models-idle", "models-computer", "models-chatty"]:
            assert (temp_dir / model_dir).exists()

        # Verify config file
        assert generator.config_file.exists()
        with open(generator.config_file) as f:
            config = json.load(f)
            assert "commands" in config
            assert "state_models" in config

    def test_config_file_formatting(self, temp_dir):
        """Test that generated config file is properly formatted."""
        generator = DefaultConfigGenerator()
        generator.generate_default_config()

        with open(generator.config_file) as f:
            content = f.read()

        # Should be pretty-printed JSON
        assert "{\n" in content  # Newline after opening brace
        assert '  "' in content  # Indented keys

    def test_wakeword_mode_mapping(self, temp_dir):
        """Test that wakewords are mapped to correct modes."""
        generator = DefaultConfigGenerator()

        # Check specific wakeword mappings
        assert generator.default_wakewords["hey_chat_tee.onnx"] == "idle"
        assert generator.default_wakewords["hey_khum_puter.onnx"] == "idle"
        assert generator.default_wakewords["okay_stop.onnx"] == "all"
        assert generator.default_wakewords["oh_kay_screenshot.onnx"] == "computer"
        assert generator.default_wakewords["wax_poetic.onnx"] == "chatty"

    def test_model_directory_contents(self, temp_dir):
        """Test that model directories contain correct wakewords."""
        generator = DefaultConfigGenerator()
        generator.generate_default_config()

        # Check models-idle directory
        idle_dir = temp_dir / "models-idle"
        idle_wakewords = [
            "hey_chat_tee.onnx",
            "hey_khum_puter.onnx",
            "okay_stop.onnx",
            "lights_on.onnx",
            "lights_off.onnx",
        ]
        for wakeword in idle_wakewords:
            assert (idle_dir / wakeword).exists() or (idle_dir / wakeword).is_symlink()

        # Check models-computer directory
        computer_dir = temp_dir / "models-computer"
        computer_wakewords = ["oh_kay_screenshot.onnx", "okay_stop.onnx"]
        for wakeword in computer_wakewords:
            assert (computer_dir / wakeword).exists() or (
                computer_dir / wakeword
            ).is_symlink()

        # Check models-chatty directory
        chatty_dir = temp_dir / "models-chatty"
        chatty_wakewords = [
            "wax_poetic.onnx",
            "thanks_chat_tee.onnx",
            "that_ill_do.onnx",
            "okay_stop.onnx",
        ]
        for wakeword in chatty_wakewords:
            assert (chatty_dir / wakeword).exists() or (
                chatty_dir / wakeword
            ).is_symlink()


class TestDefaultConfigEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create DefaultConfigGenerator instance with temp directory."""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            gen = DefaultConfigGenerator()
            return gen

    def test_wakewords_directory_already_exists(self, generator, temp_dir):
        """Test handling when wakewords directory already exists."""
        generator.wakewords_dir.mkdir(exist_ok=True)

        # Should not raise error
        try:
            generator._create_sample_wakewords()
            assert True
        except Exception:
            pytest.fail("Should handle existing directory gracefully")

    def test_symlink_creation_failure_fallback(self, generator, temp_dir):
        """Test fallback to copy when symlink creation fails."""
        # Create wakewords
        generator.wakewords_dir.mkdir(exist_ok=True)
        generator._create_sample_wakewords()

        # Create model directory
        model_dir = temp_dir / "models-idle"
        model_dir.mkdir(exist_ok=True)

        # Mock symlink_to to raise OSError
        with patch.object(
            Path, "symlink_to", side_effect=OSError("Symlink not allowed")
        ):
            # Should fallback to copy
            generator._setup_model_directories()

            # Check that files were copied instead
            for wakeword in ["hey_chat_tee.onnx", "okay_stop.onnx"]:
                target = model_dir / wakeword
                # Should exist as regular file or symlink
                assert target.exists() or target.is_symlink()

    def test_empty_wakewords_list(self, generator, temp_dir):
        """Test with empty wakewords list."""
        generator.default_wakewords = {}
        generator.wakewords_dir.mkdir(exist_ok=True)

        # Should not raise error
        generator._create_sample_wakewords()

    def test_permission_error_handling(self, generator, temp_dir):
        """Test handling of permission errors."""
        # Create read-only directory
        generator.wakewords_dir.mkdir(exist_ok=True)
        generator.wakewords_dir.chmod(0o444)

        try:
            # Should handle permission error gracefully
            generator._create_sample_wakewords()
        except PermissionError:
            # Expected on some systems
            assert True
        finally:
            # Restore permissions
            generator.wakewords_dir.chmod(0o755)

    def test_config_file_overwrite(self, generator, temp_dir):
        """Test that existing config file is overwritten."""
        # Create existing config file
        with open(generator.config_file, "w") as f:
            f.write('{"old": "config"}')

        # Generate new config
        generator._create_default_config_json()

        # Should be overwritten
        with open(generator.config_file) as f:
            content = f.read()
            assert "commands" in content
            assert "state_models" in content
