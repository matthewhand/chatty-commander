import re

with open("src/chatty_commander/llm/processor.py") as f:
    content = f.read()

# Update init type hint
content = re.sub(
    r"self\._available_suggestions_map: dict\[str, list\[str\]\] = \{\}",
    r"self._available_suggestions_map: dict[str, list[tuple[str, str]]] = {}",
    content,
)

# Update map generation
content = re.sub(
    r"self\._available_suggestions_map = \{\n                cmd: \[desc\.lower\(\) for desc in descs\]\n                for cmd, descs in self\.SUGGESTION_MAP\.items\(\)\n                if cmd in self\._available_commands\n            \}",
    r"self._available_suggestions_map = {\n                cmd: [(desc, desc.lower()) for desc in descs]\n                for cmd, descs in self.SUGGESTION_MAP.items()\n                if cmd in self._available_commands\n            }",
    content,
)

# Update usage
content = re.sub(
    r'for cmd_name, descs in self\._available_suggestions_map\.items\(\):\n            for i, desc_lower in enumerate\(descs\):\n                if partial_lower in desc_lower:\n                    suggestions\.append\(\n                        \{\n                            "command": cmd_name,\n                            "description": self\.SUGGESTION_MAP\[cmd_name\]\[i\],\n                            "confidence": 0\.7,\n                            "match_type": "keyword",\n                        \}\n                    \)',
    r'for cmd_name, descs in self._available_suggestions_map.items():\n            for desc, desc_lower in descs:\n                if partial_lower in desc_lower:\n                    suggestions.append(\n                        {\n                            "command": cmd_name,\n                            "description": desc,\n                            "confidence": 0.7,\n                            "match_type": "keyword",\n                        }\n                    )',
    content,
)

with open("src/chatty_commander/llm/processor.py", "w") as f:
    f.write(content)
