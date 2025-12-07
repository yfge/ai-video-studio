---
id: 2025-12-07T13-00-00Z-episode-schema-scenes
date: 2025-12-07T13:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episodes]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
summary: "Extend episode plan schema to carry scenes array"
---

## User Prompt

- 生成剧本时还是没有场景信息。

## Goals

- 让 episode 生成的 JSON Schema 包含 scenes 列表，促使上游 AI 返回场景信息。

## Changes

- `EpisodePlanItem` 增加可选 `scenes: List[Dict[str, Any]]` 字段，保持与 scene_count 对齐。

## Validation

- 未跑自动化；需重新触发剧集/剧本生成以验证 scenes 返回并落库。

## Next Steps

- 如仍无场景返回，需调整提示模板以明确要求输出 scenes 明细。

## Linked Commits

- (pending)
