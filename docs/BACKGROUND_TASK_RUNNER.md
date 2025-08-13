# Background Task Runner and Summary UI

## Overview

This design introduces an action for scheduling long-running commands inside ephemeral Docker containers. Users supply a `--yolo` flag with a `-p` prompt that is passed to an OpenAI Codex compatible model (default `gpt-oss:20b`). The task executes in the background, allowing the Chatty Commander interface to remain responsive.

Key goals:
- Queue and track containerized commands.
- Summarize recent log output with a separate LLM.
- Present a minimal 3‑word summary in the UI that refreshes periodically.
- Offer a kill button (square inside a circle) to terminate the job.

## Architecture

1. **Task Scheduler**
   - Accepts user request (`--yolo -p <prompt>`) and spins up a Docker container with the given command.
   - Stores metadata (start time, prompt, model, container id) in a persistent queue.

2. **Log Aggregator**
   - Streams stdout/stderr from the running container.
   - Maintains an in‑memory ring buffer of the last _N_ lines for summarization.

3. **Summary Worker**
   - Periodically invokes an LLM (`gpt-oss:20b` by default, but configurable) to summarize the ring buffer.
   - Enforces 3‑word output via regex or JSON schema.
   - Publishes summary snippets to the UI channel.

4. **UI Integration**
   - Displays a small badge with the rotating 3‑word summary for each active task.
   - Renders a stop button (square inside circle). Clicking sends a kill signal to the scheduler which stops the container and removes its UI elements.
   - When the task completes or is killed, the badge and button disappear.

## Configuration

```toml
[background_tasks]
summary_model = "gpt-oss:20b"
refresh_interval_sec = 5
ring_buffer_lines = 40
```

## Future Enhancements

- Support arbitrary model selection for both execution and summarization.
- Persist completed task logs and summaries for later review.
- Expose an API endpoint to query task status and history.
- Allow concurrent task execution with fairness policies.
