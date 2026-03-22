import pytest
from unittest.mock import patch, MagicMock
from chatty_commander.web.routes import agents

@patch("chatty_commander.web.routes.agents._LLMManager")
def test_dbg(mock_cls):
    # In the test, we patch _LLMManager class in agents module
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_json_response = """```json
    {
        "name": "Doc Summarizer",
        "description": "An expert at summarizing technical documentation.",
        "persona_prompt": "You are Doc Summarizer. You summarize docs.",
        "capabilities": ["summarize", "read_files"],
        "team_role": "summarizer"
    }
    ```"""
    mock_llm.generate_response.return_value = mock_json_response
    mock_cls.return_value = mock_llm

    # wait, agents._get_llm_manager uses global `_llm_manager`.
    # If _llm_manager was already initialized by a previous test, it won't be replaced!
    print("global _llm_manager before:", agents._llm_manager)
    agents._llm_manager = None  # Reset it
    llm = agents._get_llm_manager()
    print("llm instance:", llm)
    print("does it match mock?", llm == mock_llm)

test_dbg()
