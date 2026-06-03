# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecurringPrompt:
    id: str
    name: str
    description: str
    schedule: str
    trigger: str  # cron|webhook|manual
    context: str
    prompt: str
    variables: dict[str, Any] = field(default_factory=dict)
    response_handler: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> RecurringPrompt:
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

    def render_prompt(self, runtime_vars: dict[str, Any] | None = None) -> str:
        merged = dict(self.variables)
        if runtime_vars:
            merged.update(runtime_vars)
        rendered = self.prompt
        for key, value in merged.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered
