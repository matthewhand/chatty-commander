import json
import re

def _extract_json_from_response(response: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
    if match:
        return match.group(1).strip()
    return response.strip()

response = """```json
        {
            "name": "Doc Summarizer",
            "description": "An expert at summarizing technical documentation.",
            "persona_prompt": "You are Doc Summarizer. You summarize docs.",
            "capabilities": ["summarize", "read_files"],
            "team_role": "summarizer"
        }
        ```"""

json_str = _extract_json_from_response(response)
print("EXTRACTED:")
print(repr(json_str))
data = json.loads(json_str)
print("PARSED:")
print(data)
