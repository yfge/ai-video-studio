---
id: 2025-12-10T13-10-00Z-react-episode-story-validation
date: 2025-12-10T13:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, agent, validation]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/story_agent.py
summary: "Add ReAct-style schema validation/repair loops to story and episode LangGraph agents with richer logging."
---

## User Prompt

- “好的，现在开始做，同时尽可能输出详细的日志”

## Goals

- Make story and episode LangGraph agents self-heal JSON outputs when schema fields are missing or malformed.
- Emit clearer logs for validation/repair attempts.

## Changes

- Added ReAct-style validation loops to story/episode agents: parse, validate against Pydantic schema, and auto-reprompt the model with schema hints up to two repairs.
- Captured provider/model/usage from repair attempts and threaded detailed reasoning markers for observability.
- Logged parse/validation failures and repair attempts for episode/story generation.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Exercise episode/story generation end-to-end in a live stack to confirm repaired payloads persist to DB and logs show the new reasoning trace.
- Consider extending the same repair loop to storyboard generation if needed.

## Linked Commits

- pending
