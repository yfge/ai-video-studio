---
id: 2025-12-10T14-05-00Z-story-agent-validate-repair
date: 2025-12-10T14:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, agent, prompts]
related_paths:
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/prompts/templates/story_outline_repair.txt
  - ai-pic-backend/app/prompts/templates/story_outline_repair.yaml
  - ai-pic-backend/app/prompts/templates.py
summary: "Refactor StoryLangGraphAgent into plan->validate->repair using PromptManager-managed repair templates with missing-field hints."
---

## User Prompt

- “按这个思路重构 StoryLangGraphAgent，要求： 1. 使用提示词管理器  2. 同样有valid 以及repair 的结点”

## Goals

- Split story agent into explicit validate and repair nodes, keeping repair prompt management centralized.
- Improve repair precision by surfacing missing-field details and original prompts in repair templates.

## Changes

- Story agent now runs `plan -> validate -> repair -> END`; validate handles parse/schema check, repair re-validates or re-prompts up to three times with missing-field hints.
- Repair prompts are rendered via `PromptManager` using the new `story_outline_repair` template; `PromptTemplate` enum updated accordingly.
- Added missing-field support to repair templates (YAML/TXT) for story outlines.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Run story generation end-to-end in a live stack to observe the validate/repair reasoning trail and ensure repaired payloads persist.

## Linked Commits

- pending
