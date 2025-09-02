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

from chatty_commander.advisors.templates import (
    get_prompt_template,
    render_with_template,
)


def test_get_prompt_template_falls_back_and_renders():
    tpl = get_prompt_template(
        model="gpt-oss20b", persona_name="philosophy_advisor", api_mode="completion"
    )
    out = render_with_template(tpl, system="S", text="T")
    assert out.startswith("[tpl:stoic:completion]")
    assert "[sys] S" in out and "[user] T" in out

    # default fallback
    tpl2 = get_prompt_template(model="x", persona_name="unknown", api_mode="responses")
    out2 = render_with_template(tpl2, system="S2", text="T2")
    assert out2.startswith("[tpl:default:responses]")
