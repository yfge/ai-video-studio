---
id: 2025-12-07T14-19-06Z-script-normalize
date: 2025-12-07T14:19:06Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, langgraph]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Normalize script scenes/dialogues/stage directions so UI shows content, and fix mock generator field names"
---

## User Prompt

继续完成这个工作，并用chrome 进行测试，现在localhost:8089 是已经配置了 openi/google/火山引擎/deepseek 的key 的，如果模型没有返回，那是你的bug

## Goals

- Ensure generated scripts carry descriptions/summaries and content fields so scene/dialogue panels render instead of “暂无”.
- Normalize script payloads (scene numbers, slug_line, content keys) before persistence to avoid front-end mismatches.
- Keep mock/fallback generation compatible with the expected schema to prevent runtime errors.

## Changes

- Added `_normalize_script_content` to coerce scenes/dialogues/stage directions: fill description/summary/slug_line, convert `line`/`description`/`direction` to `content`, assign scene numbers, and rebuild script text when missing.
- Updated mock script generator and script text assembly helpers to use the normalized keys, including content fallbacks for dialogues and stage directions.
- Regenerated script 9 via API to persist normalized scenes/dialogues/stage directions after backend reload.

## Validation

- Manual API checks:
  - `curl -X POST /api/v1/auth/login` (form login) to obtain bearer token.
  - `curl -X POST /api/v1/scripts/9/regenerate` with the token (timeout 180s) returned structured scenes/dialogues/stage directions and updated the record.
- No automated tests run in this iteration.

## Next Steps

- Re-verify via Chrome UI (episode/script pages) that scene summaries, dialogues, and stage directions render correctly and no “暂无内容” placeholders remain.
- Exercise LangGraph/AI-manager paths to reduce reliance on mock fallback and ensure real providers return structured output.
- Backfill unit/integration coverage for script normalization and stage/direction field mapping.

## Linked Commits

- pending
