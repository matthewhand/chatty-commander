from chatty_commander.advisors.recurring import RecurringPrompt


def test_recurring_prompt_from_dict_and_render():
    data = {
        "id": "advisor-daily-summary",
        "name": "Daily Summary Advisor",
        "description": "Summarises the last 24 hrs of chat activity and posts to Discord.",
        "schedule": "0 9 * * *",
        "trigger": "cron",
        "context": "You are a helpful assistant. Use the provided context.",
        "prompt": "Summarise the following {{messages}}.",
        "variables": {"messages": "<ALL_MESSAGES>"},
        "response_handler": {
            "type": "post",
            "action": "sendToDiscord",
            "channel": "#daily-summary",
        },
        "metadata": {"tags": ["daily", "summary"], "owner": "alice"},
    }
    rp = RecurringPrompt.from_dict(data)
    assert rp.id == "advisor-daily-summary"
    rendered = rp.render_prompt({"messages": "Hello World"})
    assert "Hello World" in rendered
