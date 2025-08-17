# Recurring Prompts

## Blueprint

A Recurring Prompt is a small, versioned definition that can be triggered on a schedule (cron), via webhook, or manually. Store as JSON/YAML and feed to a scheduler.

Fields:

- id, name, description
- schedule (cron), trigger (cron|webhook|manual)
- context (system pre-prompt)
- prompt (supports {{variables}})
- variables (defaults)
- response_handler (post-processing contract)
- metadata (tags, owner)

Example:

```json
{
  "id": "advisor-daily-summary",
  "name": "Daily Summary Advisor",
  "description": "Summarises the last 24 hrs of chat activity and posts to Discord.",
  "schedule": "0 9 * * *",
  "trigger": "cron",
  "context": "You are a helpful assistant. Use the provided context.",
  "prompt": "Summarise the following {{messages}}.",
  "variables": { "messages": "<ALL_MESSAGES>" },
  "response_handler": {
    "type": "post",
    "action": "sendToDiscord",
    "channel": "#daily-summary"
  },
  "metadata": { "tags": ["daily", "summary"], "owner": "alice" }
}
```

## Implementation (MVP)

- Parser/rendering: `src/chatty_commander/advisors/recurring.py` with `RecurringPrompt` and `render_prompt()`.
- Tests: `tests/test_recurring_prompt.py`.
- Scheduler: out-of-repo (Node.js cron, GitHub Actions, or system cron) reads JSON, resolves variables, calls Advisors via `/api/v1/advisors/message`, then posts via bridge/webhook.

## TODO

- Add endpoint to accept recurring config upload/listing (optional)
- Add simple runner `python -m ... advisors.run_recurring --file config.json`
- Docs: example Node.js `node-cron` snippet
