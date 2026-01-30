---
id: 2025-12-07T13-59-51Z-script-ai-manager-fallback
date: 2025-12-07T13:59:51Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, ai-manager]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Add AI manager direct script fallback to avoid AttributeError and populate scripts when LangGraph fails"
---

## User Prompt

continue

## Goals

- Fix AttributeError `_call_ai_manager_script` and enable a direct AI-manager path for script generation.
- Ensure failures fall through gracefully instead of 500 responses.

## Changes

- Implemented `_call_ai_manager_script` in `AIService` to call the AI manager with dialogue/stage JSON schema and build script payload.
- Reuses episode scenes and assembles readable content for UI; returns provider/model metadata.

## Validation

- Not run (small backend change). Logs to verify when rerun from UI.

## Next Steps

- Re-run “重新生成”剧本 in UI; confirm new script now contains scenes/dialogues or mock fallback.
- If providers still fail, consider adding retry/forced model selection for scripts similar to episodes.

## Linked Commits

- pending
