import json

mock_json_response = """```json
    {
        "name": "Doc Summarizer",
        "description": "An expert at summarizing technical documentation.",
        "persona_prompt": "You are Doc Summarizer. You summarize docs.",
        "capabilities": ["summarize", "read_files"],
        "team_role": "summarizer"
    }
    ```"""

from chatty_commander.web.routes.agents import _extract_json_from_response

extracted = _extract_json_from_response(mock_json_response)
print("EXTRACTED:")
print(repr(extracted))

try:
    data = json.loads(extracted)
    print("PARSED:")
    print(data)
except Exception as e:
    print("ERROR:")
    print(e)
