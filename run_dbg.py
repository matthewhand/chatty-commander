from chatty_commander.web.routes.agents import _extract_json_from_response

response = """```json
    {
        "name": "Doc Summarizer",
        "description": "An expert at summarizing technical documentation.",
        "persona_prompt": "You are Doc Summarizer. You summarize docs.",
        "capabilities": ["summarize", "read_files"],
        "team_role": "summarizer"
    }
    ```"""
print("Extracted:")
print(_extract_json_from_response(response))

import json
try:
    data = json.loads(_extract_json_from_response(response))
    print(data)
except Exception as e:
    print("Error:", e)
