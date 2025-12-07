---
id: 2025-12-07T12-25-00Z-episode-scenes-count
date: 2025-12-07T12:25:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episodes]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
summary: "Preserve scene info from AI-generated episodes and backfill scene_count"
---

## User Prompt

- 生成剧集没有场景信息了，怀疑 schema 问题。

## Goals

- 将 AI 返回的 scenes 数组保存在剧集元数据中，并补全 scene_count。

## Changes

- 在同步/异步剧集生成中，优先使用 AI 结果中的 scene_count；若缺失则以 scenes 长度回填。
- 将 scenes 追加到 extra_metadata，避免信息丢失。
- 更新 Episode 更新/创建逻辑以统一处理该回填。

## Validation

- （逻辑小改）未跑后端自动化；前端 lint 仍通过。

## Next Steps

- 重新生成剧集或检查已有剧集的 extra_metadata.scenes 是否存在；如需前端展示场景列表，可从 extra_metadata.scenes 读取。

## Linked Commits

- (pending)
