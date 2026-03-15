import re
response = """```json
{
    "name": "Doc Summarizer",
    "description": "An expert at summarizing technical documentation.",
    "persona_prompt": "You are Doc Summarizer. You summarize docs.",
    "capabilities": ["summarize", "read_files"],
    "team_role": "summarizer"
}
```"""
match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
if match:
    print(match.group(1).strip())
