---
id: 2025-12-14T13-30-50Z-storyboard-keyframe-append
date: 2025-12-14T13:30:50Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Keep existing start/end keyframe galleries when re-running generation (append + dedupe)"
---

## User Prompt

可以（多次单张生成累积首/尾帧图集）

## Goals

- 允许多次单张首/尾帧生成时保留历史候选图，形成图集而非被覆盖。
- 保持 start/end 图集去重，兼顾现有字段兼容。

## Changes

- 在分镜首/尾帧生成任务中，持久化结果时将 start_image_urls/end_image_urls 与已有列表合并去重，并仅在缺失时回填 start_image_url/image_url/end_image_url，以保留用户已选的关键帧。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_storyboard_keyframes_schema.py`
- Chrome：已登录 `geyunfei` 后保留 `http://localhost:8089/episodes/10/storyboard` 页面可正常加载（未重复触发生成）。

## Next Steps

- 若需要验证追加效果，可在前端连续以 count=1 触发首尾帧生成，确认候选列表累积；必要时再做端到端回写检查。

## Linked Commits

- fix(backend): preserve storyboard keyframe galleries on reruns
