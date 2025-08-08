from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RecurringPrompt:
    id: str
    name: str
    description: str
    schedule: str
    trigger: str  # cron|webhook|manual
    context: str
    prompt: str
    variables: Dict[str, Any] = field(default_factory=dict)
    response_handler: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RecurringPrompt":
        required = [
            "id",
            "name",
            "description",
            "schedule",
            "trigger",
            "context",
            "prompt",
        ]
        for key in required:
            if key not in data:
                raise ValueError(f"Missing required field: {key}")
        return RecurringPrompt(
            id=str(data["id"]),
            name=str(data["name"]),
            description=str(data["description"]),
            schedule=str(data["schedule"]),
            trigger=str(data["trigger"]),
            context=str(data["context"]),
            prompt=str(data["prompt"]),
            variables=dict(data.get("variables", {})),
            response_handler=dict(data.get("response_handler", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def render_prompt(self, runtime_vars: Optional[Dict[str, Any]] = None) -> str:
        merged = dict(self.variables)
        if runtime_vars:
            merged.update(runtime_vars)
        rendered = self.prompt
        for key, value in merged.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered


