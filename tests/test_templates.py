from chatty_commander.advisors.templates import get_prompt_template, render_with_template


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
