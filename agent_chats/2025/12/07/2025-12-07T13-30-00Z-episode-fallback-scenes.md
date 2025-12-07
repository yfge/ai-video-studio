---
id: 2025-12-07T13-30-00Z-episode-fallback-scenes
date: 2025-12-07T13:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episodes]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Fallback episode prompt and mock now include scenes array"
---

## User Prompt

- 需要在剧集生成中返回场景信息，并自测端到端。

## Goals

- 确保即便走 fallback/mock 也输出 scenes 列表，便于前端展示和分镜初始化。

## Changes

- 回退 prompt 增加 scenes 字段要求与示例。
- mock episode 返回包含 scenes（含 slug_line/location/time_of_day/summary），并维持 scene_count。

## Validation

- 未跑后端自动化；需重新生成剧集验证 scenes 落库。

## Next Steps

- 重新生成剧集/剧本自测，确认 extra_metadata.scenes 存在；如仍缺失，检查 AI manager 密钥并观察真实模型返回。

## Linked Commits

- (pending)
