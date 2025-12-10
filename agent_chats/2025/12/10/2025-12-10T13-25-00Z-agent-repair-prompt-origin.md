---
id: 2025-12-10T13-25-00Z-agent-repair-prompt-origin
date: 2025-12-10T13:25:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, agent]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/story_agent.py
summary: "Include original prompts in LangGraph repair loops for better JSON self-healing context."
---

## User Prompt

- “repair_prompt 是不是应该有原始的提示词？”

## Goals

- Feed the original generation prompt into the ReAct-style repair step so the model can reconcile schema errors with initial intent.

## Changes

- Episode/story agents now pass the originating prompt into repair prompts, alongside schema and raw output, during validation retries.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Observe repair logs in a live stack to confirm prompts surface correctly and reduce schema failures. Extend to storyboard if needed.

## Linked Commits

- pending
