---
id: 2025-12-07T13-55-50Z-script-fallback
date: 2025-12-07T13:55:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, langgraph]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
summary: "Guard LangGraph script generation: if scenes/dialogues missing, abort to fallback instead of saving empty scripts"
---

## User Prompt

continue

## Goals

- Prevent empty scripts from being persisted when LangGraph script agent fails.
- Allow downstream fallbacks (direct AI or mock) to run instead of accepting incomplete output.

## Changes

- Added validation after LangGraph execution to require content with scenes and dialogues; otherwise return None and log warnings.

## Validation

- Not run (backend change only); relies on existing CI/lint.

## Next Steps

- Re-run script generation from the UI to confirm fallbacks now populate full text.
- If failures persist, add provider retry/selection handling in script generation.

## Linked Commits

- pending
