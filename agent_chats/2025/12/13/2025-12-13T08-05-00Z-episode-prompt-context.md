---
id: 2025-12-13T08-05-00Z-episode-prompt-context
date: 2025-12-13T08:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episode, prompt]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline.yaml
summary: "Added prior-episode context and character references into episode generation prompt."
---

## User Prompt

每一集的生成提示词中应该包括之前的剧集概要的列表吧还有角色，而不是只有故事

## Goals

- 在剧集生成提示中加入前序集概要（logline）和角色信息，保证连贯。

## Changes

- `episode_from_outline` 模板加入角色列表、主冲突、重点角色和前序集（标题+logline）提示。
- Episode agent 在渲染 prompt 时传入 `previous_episodes`（按 episode_number 排序过滤当前集之前）。

## Validation

- 未跑新增测试（改动为 prompt/context 追加，不影响 schema）；后续需在 E2E/手动生成中验证连贯性。

## Next Steps

- 重新跑端到端剧集生成，确认 prompt 含前序集与角色信息。

## Linked Commits

- TODO: add commit hash after commit
