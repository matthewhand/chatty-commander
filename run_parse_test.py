import sys
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
print(repr(_extract_json_from_response(response)))
