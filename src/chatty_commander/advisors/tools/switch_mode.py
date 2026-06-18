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

try:
    from agents import FunctionTool

    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


def switch_mode(mode: str) -> str:
    mode = (mode or "").strip()
    if not mode:
        return "SWITCH_MODE:invalid"
    return f"SWITCH_MODE:{mode}"


# FunctionTool instance for the openai-agents SDK, mirroring dograh_call.
# AdvisorsService.handle_message intercepts the returned "SWITCH_MODE:<mode>"
# directive and performs the actual state transition.
switch_mode_tool_instance = None
if AGENTS_AVAILABLE:
    switch_mode_tool_instance = FunctionTool(
        name="switch_mode",
        description=(
            "Switch ChattyCommander into a different operating mode (e.g. "
            "'idle', 'computer', 'chatty'). Use this when the user asks to "
            "change modes. Returns a SWITCH_MODE directive that the service "
            "layer executes."
        ),
        params_json_schema={
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Name of the mode/state to switch to.",
                },
            },
            "required": ["mode"],
        },
        on_invoke_tool=switch_mode,  # type: ignore[arg-type]
    )

