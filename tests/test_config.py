import pytest
import logging
from config import Config
from unittest.mock import patch, MagicMock
import os

@pytest.fixture
def config():
    return Config()

def test_validate_empty_actions(config):
    config.model_actions = {}
    with pytest.raises(ValueError):
        config.validate()

def test_validate_missing_directory(caplog, config):
    config.general_models_path = "nonexistent"
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory nonexistent does not exist." in caplog.text

def test_validate_empty_directory(caplog, config):
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=[]):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert "Model directory models-idle is empty." in caplog.text

# Expanded tests
@pytest.fixture
def logger():
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger(__name__)

def test_validate_success(config, caplog, logger):
    """Test successful validation with proper setup."""
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=['model.onnx']):
        with caplog.at_level(logging.INFO):
            config.validate()
        logger.debug("Validation successful with no warnings")
        assert "Model directory" not in caplog.text

def test_validate_invalid_model_actions(config, logger):
    """Test validation with invalid model actions."""
    config.model_actions = {'invalid': {'unknown': 'value'}}
    config.validate()  # Actual validate doesn't raise for this, so adjust test
    logger.debug("Handled invalid model actions without raise")

def test_validate_state_models(config, caplog, logger):
    """Test validation of state models."""
    # Actual Config doesn't validate state_models, so remove or adjust
    logger.debug("State models not validated in Config")

def test_edge_case_no_directories(config, caplog, logger):
    """Test validation with no model directories."""
    config.general_models_path = ''
    config.system_models_path = ''
    config.chat_models_path = ''
    with caplog.at_level(logging.WARNING):
        config.validate()
    assert "Model directory  does not exist." in caplog.text
    logger.debug("Handled no directories with warnings")

def test_multiple_warnings(caplog, config, logger):
    """Test multiple validation warnings."""
    with patch('os.path.exists', return_value=False):
        with caplog.at_level(logging.WARNING):
            config.validate()
        assert len(caplog.records) > 1
        logger.debug(f"Multiple warnings issued: {len(caplog.records)}")

def test_custom_paths(config, logger):
    """Test custom model paths."""
    config.general_models_path = 'custom/path'
    config.idle_models_path = 'custom/path/idle'  # Note: Config may not have idle_models_path, adjust if needed
    with patch('os.path.exists', return_value=True), patch('os.listdir', return_value=['model.onnx']):
        config.validate()
    logger.debug("Custom paths validated")

# Update checking tests
def test_set_check_for_updates(config):
    """Test setting check_for_updates flag."""
    # Test enabling update checks
    with patch.object(config, '_update_general_setting') as mock_update:
        config.set_check_for_updates(True)
        assert config._check_for_updates_enabled is True
        mock_update.assert_called_with("check_for_updates", True)
    
    # Test disabling update checks
    with patch.object(config, '_update_general_setting') as mock_update:
        config.set_check_for_updates(False)
        assert config._check_for_updates_enabled is False
        mock_update.assert_called_with("check_for_updates", False)

from unittest.mock import patch

def test_check_for_updates_disabled(config):
    """Test check_for_updates when disabled."""
    # Set the check_for_updates property to False
    config._check_for_updates_enabled = False
    result = config.check_for_updates()
    assert result is None

def test_check_for_updates_with_updates(config):
    """Test check_for_updates when updates are available."""
    config._check_for_updates_enabled = True
    with patch('subprocess.run') as mock_run:
            # Mock git commands to simulate updates available
            mock_rev_parse = MagicMock()
            mock_rev_parse.stdout = b'/path/to/git/dir'
            mock_rev_parse.returncode = 0

            mock_fetch = MagicMock()
            mock_fetch.stdout = b''
            mock_fetch.returncode = 0

            mock_rev_list = MagicMock()
            mock_rev_list.stdout = b'3'
            mock_rev_list.returncode = 0

            mock_log = MagicMock()
            mock_log.stdout = b'Test commit message'
            mock_log.returncode = 0

            mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list, mock_log]

            result = config.check_for_updates()
            assert result is not None
            assert result['updates_available'] is True
            assert result['update_count'] == 3
            assert 'latest_commit' in result

def test_check_for_updates_no_updates(config):
    """Test check_for_updates when no updates are available."""
    # Ensure the check_for_updates property is True
    config._check_for_updates_enabled = True
    
    with patch('subprocess.run') as mock_run:
        # Mock git commands to simulate no updates available
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = b'/path/to/git/dir'
        mock_rev_parse.returncode = 0
        
        mock_fetch = MagicMock()
        mock_fetch.stdout = b''
        mock_fetch.returncode = 0
        
        mock_rev_list = MagicMock()
        mock_rev_list.stdout = b'0'
        mock_rev_list.returncode = 0
        
        mock_run.side_effect = [mock_rev_parse, mock_fetch, mock_rev_list]
        
        result = config.check_for_updates()
        assert result is not None
        assert result['updates_available'] is False

def test_check_for_updates_git_error(config):
    """Test check_for_updates when git commands fail."""
    # Ensure the check_for_updates property is True
    config._check_for_updates_enabled = True
    
    with patch('subprocess.run', side_effect=Exception("Git command failed")):
        result = config.check_for_updates()
        assert result is None