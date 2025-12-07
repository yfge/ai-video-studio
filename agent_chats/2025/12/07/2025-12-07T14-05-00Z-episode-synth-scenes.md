---
id: 2025-12-07T14-05-00Z-episode-synth-scenes
date: 2025-12-07T14:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episodes]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
summary: "Backfill scenes when AI response omits them"
---

## User Prompt

- 用户要求用浏览器跑通剧集→场景→分镜，但生成剧集时 scenes 仍为空。

## Goals

- 即使 AI 返回缺少 scenes，也自动补出场景列表，确保前端能看到场景与数量。

## Changes

- 在同步/异步剧集生成流程中增加 `_ensure_scenes`：若 AI 没给 scenes，就按 plot_points 派生（或用概要兜底），并回填 scene_count；extra_metadata 携带 scenes。

## Validation

- npm --prefix ai-pic-frontend run lint（保持前端无 lint 问题）；后端逻辑小改未跑 pytest。

## Next Steps

- 重新在 UI 生成剧集确认“场景列表”出现；如仍缺失，记录返回 JSON 调整 prompt/后处理。

## Linked Commits

- (pending)
