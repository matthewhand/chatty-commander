import json
from unittest.mock import MagicMock
import pytest

from chatty_commander.llm.processor import CommandProcessor

@pytest.fixture
def mock_llm_manager():
    return MagicMock()

@pytest.fixture
def mock_config_manager():
    config = MagicMock()
    config.model_actions = {
        "lights": {"action": "voice_chat"},
        "music": {"action": "voice_chat"},
        "weather": {"action": "voice_chat"},
        "test_cmd": {"action": "voice_chat"},
    }
    return config

@pytest.fixture
def processor(mock_llm_manager, mock_config_manager):
    return CommandProcessor(llm_manager=mock_llm_manager, config_manager=mock_config_manager)

def test_simple_match_exact(processor):
    cmd, conf, reason = processor.process_command("lights")
    assert cmd == "lights"
    assert conf == 0.9

def test_simple_match_keyword(processor):
    cmd, conf, reason = processor.process_command("turn on the lamp")
    assert cmd == "lights"
    assert conf == 0.7

def test_llm_interpretation_success(processor):
    processor.llm_manager.is_available.return_value = True
    processor.llm_manager.generate_response.return_value = json.dumps({
        "command": "test_cmd",
        "confidence": 0.85,
        "reasoning": "Test reasoning"
    })
    cmd, conf, reason = processor.process_command("execute test command")
    assert cmd == "test_cmd"
    assert conf == 0.85
    assert reason == "Test reasoning"

def test_llm_interpretation_unknown_command(processor):
    processor.llm_manager.is_available.return_value = True
    processor.llm_manager.generate_response.return_value = json.dumps({
        "command": "unknown_cmd",
        "confidence": 0.9,
        "reasoning": "bad logic"
    })
    cmd, conf, reason = processor.process_command("something weird")
    assert cmd is None
    assert conf == 0.0
    assert "LLM suggested unknown command" in reason

def test_llm_interpretation_invalid_json(processor):
    processor.llm_manager.is_available.return_value = True
    processor.llm_manager.generate_response.return_value = "Not JSON"
    cmd, conf, reason = processor.process_command("broken response")
    assert cmd is None
    assert conf == 0.0
    assert "No JSON found" in reason

def test_suggestions_partial_name(processor):
    suggestions = processor.get_command_suggestions("lig")
    assert len(suggestions) > 0
    assert suggestions[0]["command"] == "lights"
    assert suggestions[0]["match_type"] == "name"

def test_suggestions_keyword(processor):
    suggestions = processor.get_command_suggestions("illumination")
    found = any(s["command"] == "lights" for s in suggestions)
    assert found

def test_explain_command(processor):
    explanation = processor.explain_command("lights")
    assert explanation["command"] == "lights"
    assert explanation["type"] == "action"

def test_get_processor_status(processor):
    status = processor.get_processor_status()
    assert status["commands_count"] == 4
    assert "llm_available" in status