from chatty_commander.web.routes.agents import parse_blueprint_from_text

class MockLLM:
    def is_available(self): return True
    def generate_response(self, text):
        return """```json
    {
        "name": "Doc Summarizer",
        "description": "An expert at summarizing technical documentation.",
        "persona_prompt": "You are Doc Summarizer. You summarize docs.",
        "capabilities": ["summarize", "read_files"],
        "team_role": "summarizer"
    }
    ```"""

import chatty_commander.web.routes.agents as mod
mod._llm_manager = MockLLM()
bp = parse_blueprint_from_text("My helpful agent who summarizes docs")
print(bp)
