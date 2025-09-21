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
Comprehensive tests for app default configuration module.

Tests configuration loading, validation, merging, and management.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest

from src.chatty_commander.app.default_config import (
    ConfigLoader,
    ConfigMerger,
    ConfigSchema,
    ConfigSection,
    ConfigValidator,
    DefaultConfig,
)


class TestConfigSection:
    """Test ConfigSection class."""

    def test_config_section_creation(self):
        """Test creating a ConfigSection instance."""
        section = ConfigSection(
            name="test_section",
            data={"key": "value", "number": 42},
            description="A test configuration section",
            required=True,
            version="1.0.0",
        )

        assert section.name == "test_section"
        assert section.data == {"key": "value", "number": 42}
        assert section.description == "A test configuration section"
        assert section.required is True
        assert section.version == "1.0.0"

    def test_config_section_defaults(self):
        """Test ConfigSection with default values."""
        section = ConfigSection(name="simple_section", data={})

        assert section.name == "simple_section"
        assert section.data == {}
        assert section.description == ""
        assert section.required is False
        assert section.version == "1.0.0"

    def test_config_section_to_dict(self):
        """Test converting ConfigSection to dictionary."""
        section = ConfigSection(
            name="dict_section",
            data={"test": "data"},
            description="Test section",
            required=True,
            version="2.0.0",
        )

        section_dict = section.to_dict()

        assert section_dict["name"] == "dict_section"
        assert section_dict["data"] == {"test": "data"}
        assert section_dict["description"] == "Test section"
        assert section_dict["required"] is True
        assert section_dict["version"] == "2.0.0"

    def test_config_section_from_dict(self):
        """Test creating ConfigSection from dictionary."""
        section_dict = {
            "name": "dict_section",
            "data": {"test": "data"},
            "description": "Test section",
            "required": True,
            "version": "2.0.0",
        }

        section = ConfigSection.from_dict(section_dict)

        assert section.name == "dict_section"
        assert section.data == {"test": "data"}
        assert section.description == "Test section"
        assert section.required is True
        assert section.version == "2.0.0"

    def test_config_section_get_set_item(self):
        """Test dictionary-like access to ConfigSection."""
        section = ConfigSection(name="access_test", data={"key1": "value1"})

        # Test getting existing item
        assert section["key1"] == "value1"

        # Test getting non-existing item
        assert section["nonexistent"] is None

        # Test setting item
        section["key2"] = "value2"
        assert section["key2"] == "value2"

        # Test setting nested item
        section["nested.key"] = "nested_value"
        assert section["nested.key"] == "nested_value"

    def test_config_section_merge(self):
        """Test merging ConfigSection with another."""
        section1 = ConfigSection(name="merge1", data={"a": 1, "b": 2})
        section2 = ConfigSection(name="merge2", data={"b": 3, "c": 4})

        merged = section1.merge(section2)

        assert merged["a"] == 1  # From section1
        assert merged["b"] == 3  # From section2 (overridden)
        assert merged["c"] == 4  # From section2


class TestConfigSchema:
    """Test ConfigSchema class."""

    def test_config_schema_creation(self):
        """Test creating a ConfigSchema instance."""
        schema = ConfigSchema(
            sections=["core", "ui", "advanced"],
            version="1.0.0",
            required_sections=["core"],
            optional_sections=["ui", "advanced"],
            validation_rules={"core.timeout": "integer"},
        )

        assert schema.sections == ["core", "ui", "advanced"]
        assert schema.version == "1.0.0"
        assert schema.required_sections == ["core"]
        assert schema.optional_sections == ["ui", "advanced"]
        assert schema.validation_rules == {"core.timeout": "integer"}

    def test_config_schema_defaults(self):
        """Test ConfigSchema with default values."""
        schema = ConfigSchema(sections=["core"])

        assert schema.sections == ["core"]
        assert schema.version == "1.0.0"
        assert schema.required_sections == ["core"]
        assert schema.optional_sections == []
        assert schema.validation_rules == {}

    def test_config_schema_validate(self):
        """Test ConfigSchema validation."""
        schema = ConfigSchema(
            sections=["core", "ui"],
            required_sections=["core"],
            validation_rules={"core.timeout": "integer"},
        )

        # Valid schema
        assert schema.validate() is True

        # Invalid schema (missing required section)
        invalid_schema = ConfigSchema(
            sections=["ui"],
            required_sections=["core"],  # Missing required "core"
        )
        assert invalid_schema.validate() is False

    def test_config_schema_to_dict(self):
        """Test converting ConfigSchema to dictionary."""
        schema = ConfigSchema(
            sections=["core", "ui"],
            version="2.0.0",
            required_sections=["core"],
            validation_rules={"core.timeout": "integer", "ui.theme": "string"},
        )

        schema_dict = schema.to_dict()

        assert schema_dict["sections"] == ["core", "ui"]
        assert schema_dict["version"] == "2.0.0"
        assert schema_dict["required_sections"] == ["core"]
        assert schema_dict["validation_rules"] == {
            "core.timeout": "integer",
            "ui.theme": "string",
        }


class TestConfigValidator:
    """Test ConfigValidator class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "core": {"timeout": 30, "retries": 3, "debug": False},
            "ui": {"theme": "dark", "language": "en"},
        }

    @pytest.fixture
    def validation_rules(self):
        """Create validation rules for testing."""
        return {
            "core.timeout": "integer",
            "core.retries": "integer",
            "core.debug": "boolean",
            "ui.theme": "string",
            "ui.language": "string",
        }

    def test_config_validator_initialization(self, validation_rules):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator(validation_rules)

        assert validator.validation_rules == validation_rules
        assert validator.custom_validators == {}

    def test_validate_config_valid(self, sample_config, validation_rules):
        """Test validating valid configuration."""
        validator = ConfigValidator(validation_rules)

        result = validator.validate_config(sample_config)

        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_config_invalid(self, validation_rules):
        """Test validating invalid configuration."""
        validator = ConfigValidator(validation_rules)

        invalid_config = {
            "core": {
                "timeout": "thirty",  # Should be integer
                "retries": 3,
                "debug": False,
            },
            "ui": {"theme": 123, "language": "en"},  # Should be string
        }

        result = validator.validate_config(invalid_config)

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert "timeout" in str(result["errors"])
        assert "theme" in str(result["errors"])

    def test_add_custom_validator(self, validation_rules):
        """Test adding custom validator."""
        validator = ConfigValidator(validation_rules)

        def custom_port_validator(value):
            return isinstance(value, int) and 1 <= value <= 65535

        validator.add_custom_validator("core.port", custom_port_validator)

        assert "core.port" in validator.custom_validators

    def test_validate_with_custom_validators(self):
        """Test validation with custom validators."""
        validation_rules = {"core.port": "integer"}
        validator = ConfigValidator(validation_rules)

        def custom_port_validator(value):
            return isinstance(value, int) and 1 <= value <= 65535

        validator.add_custom_validator("core.port", custom_port_validator)

        # Valid port
        valid_config = {"core": {"port": 8080}}
        result = validator.validate_config(valid_config)
        assert result["valid"] is True

        # Invalid port
        invalid_config = {"core": {"port": 99999}}  # Too high
        result = validator.validate_config(invalid_config)
        assert result["valid"] is False

    def test_validate_missing_required_fields(self, validation_rules):
        """Test validation with missing required fields."""
        validator = ConfigValidator(validation_rules)

        incomplete_config = {
            "core": {
                "timeout": 30
                # Missing retries and debug
            }
        }

        result = validator.validate_config(incomplete_config)

        # Should still be valid if validation rules are satisfied
        assert result["valid"] is True  # Only validates defined rules

    def test_validate_empty_config(self):
        """Test validating empty configuration."""
        validator = ConfigValidator({})

        result = validator.validate_config({})

        assert result["valid"] is True
        assert result["errors"] == []


class TestConfigMerger:
    """Test ConfigMerger class."""

    @pytest.fixture
    def base_config(self):
        """Create base configuration for testing."""
        return {
            "core": {"timeout": 30, "retries": 3, "debug": False},
            "ui": {"theme": "light"},
        }

    @pytest.fixture
    def override_config(self):
        """Create override configuration for testing."""
        return {
            "core": {"timeout": 60, "debug": True},  # Override  # Override
            "new_section": {"feature": "enabled"},  # Addition
        }

    def test_config_merger_initialization(self):
        """Test ConfigMerger initialization."""
        merger = ConfigMerger()

        assert merger.merge_strategies == {}
        assert merger.conflict_resolvers == {}

    def test_merge_configs_basic(self, base_config, override_config):
        """Test basic configuration merging."""
        merger = ConfigMerger()

        merged = merger.merge_configs(base_config, override_config)

        assert merged["core"]["timeout"] == 60  # Overridden
        assert merged["core"]["retries"] == 3  # Preserved
        assert merged["core"]["debug"] is True  # Overridden
        assert merged["ui"]["theme"] == "light"  # Preserved
        assert merged["new_section"]["feature"] == "enabled"  # Added

    def test_merge_configs_with_strategy(self, base_config, override_config):
        """Test merging with custom strategy."""
        merger = ConfigMerger()

        def take_max_strategy(base_val, override_val):
            if isinstance(base_val, (int, float)) and isinstance(
                override_val, (int, float)
            ):
                return max(base_val, override_val)
            return override_val  # Default to override

        merger.add_merge_strategy("core.timeout", take_max_strategy)

        merged = merger.merge_configs(base_config, override_config)

        # 60 (override) should still win since take_max_strategy defaults to override
        assert merged["core"]["timeout"] == 60

    def test_merge_configs_with_conflict_resolver(self, base_config, override_config):
        """Test merging with conflict resolver."""
        merger = ConfigMerger()

        def prefer_base_resolver(base_val, override_val):
            return base_val  # Always prefer base value

        merger.add_conflict_resolver("core.timeout", prefer_base_resolver)

        merged = merger.merge_configs(base_config, override_config)

        assert merged["core"]["timeout"] == 30  # Base value preserved

    def test_merge_configs_deep_merge(self, base_config, override_config):
        """Test deep merging of nested configurations."""
        merger = ConfigMerger()

        # Add nested override
        nested_override = {"core": {"nested": {"value": "new_nested"}}}

        merged = merger.merge_configs(base_config, nested_override)

        assert merged["core"]["nested"]["value"] == "new_nested"

    def test_merge_configs_with_lists(self):
        """Test merging configurations containing lists."""
        merger = ConfigMerger()

        base_config = {"features": ["feature1", "feature2"]}

        override_config = {"features": ["feature3", "feature4"]}

        merged = merger.merge_configs(base_config, override_config)

        # Lists should be replaced, not merged
        assert merged["features"] == ["feature3", "feature4"]


class TestConfigLoader:
    """Test ConfigLoader class."""

    @pytest.fixture
    def temp_config_files(self, tmp_path):
        """Create temporary configuration files for testing."""
        # JSON config
        json_file = tmp_path / "config.json"
        json_file.write_text('{"core": {"timeout": 30}, "ui": {"theme": "dark"}}')

        # YAML config
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            """
core:
  timeout: 60
  retries: 5
ui:
  theme: light
  language: en
"""
        )

        # INI config
        ini_file = tmp_path / "config.ini"
        ini_file.write_text(
            """
[core]
timeout = 45
retries = 3

[ui]
theme = blue
language = es
"""
        )

        return {"json": str(json_file), "yaml": str(yaml_file), "ini": str(ini_file)}

    def test_config_loader_initialization(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader()

        assert loader.supported_formats == ["json", "yaml", "ini", "toml"]
        assert loader.default_paths == []

    def test_load_json_config(self, temp_config_files):
        """Test loading JSON configuration."""
        loader = ConfigLoader()

        config = loader.load_config(temp_config_files["json"])

        assert config["core"]["timeout"] == 30
        assert config["ui"]["theme"] == "dark"

    def test_load_config_from_multiple_sources(self, temp_config_files):
        """Test loading configuration from multiple sources."""
        loader = ConfigLoader()

        # Load from JSON and then override with YAML
        base_config = loader.load_config(temp_config_files["json"])
        override_config = loader.load_config(temp_config_files["yaml"])

        # Merge configurations
        merger = ConfigMerger()
        merged = merger.merge_configs(base_config, override_config)

        assert merged["core"]["timeout"] == 60  # From YAML (override)
        assert merged["core"]["retries"] == 5  # From YAML (addition)
        assert merged["ui"]["theme"] == "light"  # From YAML (override)

    def test_load_config_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = ConfigLoader()

        config = loader.load_config("nonexistent.json")

        assert config == {}

    def test_detect_config_format(self):
        """Test detecting configuration file format."""
        loader = ConfigLoader()

        assert loader.detect_format("config.json") == "json"
        assert loader.detect_format("config.yaml") == "yaml"
        assert loader.detect_format("config.ini") == "ini"
        assert loader.detect_format("config.toml") == "toml"
        assert loader.detect_format("config.txt") == "unknown"

    def test_load_config_from_environment(self):
        """Test loading configuration from environment variables."""
        loader = ConfigLoader()

        # Set environment variables
        env_vars = {
            "CHATTY_CORE_TIMEOUT": "90",
            "CHATTY_UI_THEME": "env_theme",
            "CHATTY_DEBUG_MODE": "true",
        }

        with patch.dict(os.environ, env_vars):
            config = loader.load_config_from_environment("CHATTY_")

            assert config["core"]["timeout"] == "90"
            assert config["ui"]["theme"] == "env_theme"
            assert config["debug"]["mode"] == "true"

    def test_load_config_with_fallbacks(self, temp_config_files):
        """Test loading configuration with fallback sources."""
        loader = ConfigLoader()

        # Try to load from multiple paths with fallbacks
        config_paths = [
            "nonexistent1.json",  # Doesn't exist
            temp_config_files["json"],  # Exists
            "nonexistent2.json",  # Doesn't exist
        ]

        config = loader.load_config_with_fallbacks(config_paths)

        assert config["core"]["timeout"] == 30  # From the existing file
        assert config["ui"]["theme"] == "dark"


class TestDefaultConfig:
    """Test DefaultConfig class."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary configuration directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create default config files
        default_config = config_dir / "default.json"
        default_config.write_text(
            '{"core": {"timeout": 30}, "ui": {"theme": "default"}}'
        )

        user_config = config_dir / "user.json"
        user_config.write_text(
            '{"core": {"timeout": 60}, "custom": {"feature": "enabled"}}'
        )

        return str(config_dir)

    def test_default_config_initialization(self):
        """Test DefaultConfig initialization."""
        config = DefaultConfig()

        assert config.config == {}
        assert config.loaded_files == []
        assert config.validation_errors == []

    def test_load_default_config(self):
        """Test loading default configuration."""
        config = DefaultConfig()

        # Load minimal default config
        result = config.load_defaults()

        assert result is True
        assert "core" in config.config
        assert "ui" in config.config

    def test_load_from_file(self, temp_config_dir):
        """Test loading configuration from file."""
        config = DefaultConfig()

        config_path = f"{temp_config_dir}/default.json"
        result = config.load_from_file(config_path)

        assert result is True
        assert config.config["core"]["timeout"] == 30
        assert config.config["ui"]["theme"] == "default"

    def test_load_from_multiple_files(self, temp_config_dir):
        """Test loading from multiple configuration files."""
        config = DefaultConfig()

        # Load base config
        config.load_from_file(f"{temp_config_dir}/default.json")

        # Load user config (should merge)
        config.load_from_file(f"{temp_config_dir}/user.json")

        assert config.config["core"]["timeout"] == 60  # Overridden
        assert config.config["ui"]["theme"] == "default"  # Preserved
        assert config.config["custom"]["feature"] == "enabled"  # Added

    def test_merge_with_user_config(self, temp_config_dir):
        """Test merging with user configuration."""
        config = DefaultConfig()

        # Load defaults
        config.load_defaults()

        # Merge with user config
        user_config = {"core": {"timeout": 45}, "user_feature": {"enabled": True}}
        config.merge_user_config(user_config)

        assert config.config["core"]["timeout"] == 45  # Merged
        assert "user_feature" in config.config  # Added

    def test_validate_config(self):
        """Test configuration validation."""
        config = DefaultConfig()

        # Load some config
        config.config = {"core": {"timeout": 30, "retries": 3}, "ui": {"theme": "dark"}}

        # Mock validator
        validator = Mock()
        validator.validate_config.return_value = {"valid": True, "errors": []}

        with patch(
            "src.chatty_commander.app.default_config.ConfigValidator"
        ) as mock_validator_class:
            mock_validator_class.return_value = validator

            result = config.validate()

            assert result is True
            validator.validate_config.assert_called_once()

    def test_get_config_value(self):
        """Test getting configuration values."""
        config = DefaultConfig()

        config.config = {"core": {"timeout": 30, "nested": {"value": "test"}}}

        # Test simple value
        assert config.get("core.timeout") == 30

        # Test nested value
        assert config.get("core.nested.value") == "test"

        # Test default value
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_config_value(self):
        """Test setting configuration values."""
        config = DefaultConfig()

        config.config = {"core": {"timeout": 30}}

        # Set simple value
        config.set("core.timeout", 60)
        assert config.get("core.timeout") == 60

        # Set nested value
        config.set("core.new_nested.value", "new_value")
        assert config.get("core.new_nested.value") == "new_value"

    def test_save_config(self, temp_config_dir):
        """Test saving configuration to file."""
        config = DefaultConfig()

        config.config = {"core": {"timeout": 45}, "ui": {"theme": "saved"}}

        save_path = f"{temp_config_dir}/saved_config.json"
        result = config.save_to_file(save_path)

        assert result is True

        # Verify file contents
        with open(save_path) as f:
            saved_config = json.load(f)

        assert saved_config["core"]["timeout"] == 45
        assert saved_config["ui"]["theme"] == "saved"

    def test_export_config_formats(self, temp_config_dir):
        """Test exporting configuration in different formats."""
        config = DefaultConfig()

        config.config = {"core": {"timeout": 30}, "ui": {"theme": "export_test"}}

        # Export as JSON
        json_path = f"{temp_config_dir}/export.json"
        config.export_config(json_path, format="json")

        # Export as YAML
        yaml_path = f"{temp_config_dir}/export.yaml"
        config.export_config(yaml_path, format="yaml")

        # Verify JSON export
        assert json_path.exists()
        with open(json_path) as f:
            json_config = json.load(f)
        assert json_config["core"]["timeout"] == 30

        # Verify YAML export
        assert yaml_path.exists()
        with open(yaml_path) as f:
            yaml_content = f.read()
        assert "timeout: 30" in yaml_content

    def test_get_config_summary(self):
        """Test getting configuration summary."""
        config = DefaultConfig()

        config.config = {
            "core": {"timeout": 30, "retries": 3, "debug": False},
            "ui": {"theme": "dark", "language": "en"},
            "features": ["feature1", "feature2"],
        }

        summary = config.get_summary()

        assert "total_sections" in summary
        assert "total_settings" in summary
        assert "format_supported" in summary
        assert summary["total_sections"] == 3
        assert summary["total_settings"] == 6  # 3 core + 2 ui + 1 features

    def test_config_backup_restore(self, temp_config_dir):
        """Test configuration backup and restore."""
        config = DefaultConfig()

        # Set initial config
        config.config = {"initial": {"value": "original"}}
        config.loaded_files = ["original.json"]

        backup_path = f"{temp_config_dir}/config_backup.json"

        # Create backup
        backup_result = config.backup(backup_path)
        assert backup_result is True

        # Modify config
        config.config = {"modified": {"value": "changed"}}
        config.loaded_files = ["modified.json"]

        # Restore from backup
        restore_result = config.restore(backup_path)
        assert restore_result is True

        # Verify restoration
        assert config.config["initial"]["value"] == "original"
        assert config.loaded_files == ["original.json"]

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        config = DefaultConfig()

        # Modify config
        config.config = {"custom": {"setting": "modified"}}
        config.loaded_files = ["custom.json"]

        # Reset to defaults
        config.reset_to_defaults()

        assert config.config == {}  # Should be empty
        assert config.loaded_files == []

    def test_get_config_diff(self, temp_config_dir):
        """Test getting configuration differences."""
        config = DefaultConfig()

        # Set base config
        config.config = {"core": {"timeout": 30}}

        # Create another config for comparison
        other_config = {
            "core": {"timeout": 60},  # Different
            "ui": {"theme": "dark"},  # Added
        }

        diff = config.get_diff(other_config)

        assert "core.timeout" in diff
        assert "ui.theme" in diff
        assert diff["core.timeout"]["old"] == 30
        assert diff["core.timeout"]["new"] == 60

    def test_config_environment_override(self):
        """Test environment variable overrides."""
        config = DefaultConfig()

        config.config = {"core": {"timeout": 30}, "ui": {"theme": "default"}}

        # Mock environment variables
        env_overrides = {"CHATTY_CORE_TIMEOUT": "90", "CHATTY_UI_THEME": "env_theme"}

        with patch.dict(os.environ, env_overrides):
            config.apply_environment_overrides("CHATTY_")

        assert config.get("core.timeout") == "90"  # String from env
        assert config.get("ui.theme") == "env_theme"

    def test_config_type_conversion(self):
        """Test configuration value type conversion."""
        config = DefaultConfig()

        config.config = {
            "core": {
                "timeout": "30",  # String
                "retries": "3",  # String
                "debug": "false",  # String
            }
        }

        # Convert types
        type_hints = {"core.timeout": int, "core.retries": int, "core.debug": bool}

        config.convert_types(type_hints)

        assert config.get("core.timeout") == 30
        assert config.get("core.retries") == 3
        assert config.get("core.debug") is False

    def test_config_search_functionality(self):
        """Test configuration search functionality."""
        config = DefaultConfig()

        config.config = {
            "core": {"timeout": 30, "debug_mode": True, "max_connections": 100},
            "ui": {"theme": "dark", "language": "en"},
        }

        # Search for timeout settings
        timeout_results = config.search("timeout")
        assert len(timeout_results) == 1
        assert timeout_results[0]["path"] == "core.timeout"

        # Search for boolean settings
        bool_results = config.search("mode")
        assert len(bool_results) == 1
        assert bool_results[0]["path"] == "core.debug_mode"

    def test_config_statistics(self):
        """Test configuration statistics."""
        config = DefaultConfig()

        config.config = {
            "core": {
                "timeout": 30,
                "retries": 3,
                "debug": False,
                "nested": {"value1": "test1", "value2": "test2"},
            },
            "ui": {"theme": "dark", "features": ["a", "b", "c"]},
        }

        stats = config.get_statistics()

        assert stats["total_sections"] == 2
        assert stats["total_settings"] == 8  # 4 core + 2 ui + 2 nested
        assert stats["max_depth"] == 2
        assert stats["data_types"]["int"] == 2  # timeout, retries
        assert stats["data_types"]["bool"] == 1  # debug
        assert stats["data_types"]["str"] == 3  # theme, value1, value2
        assert stats["data_types"]["list"] == 1  # features
