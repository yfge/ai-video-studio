---
id: 2025-12-19T06-24-54Z-i2v-polling-timeout
date: 2025-12-19T06:24:54Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, polling]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider/video.py
  - ai-pic-backend/app/services/providers/minimax_provider/video.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video.py
summary: "Extend image-to-video polling windows to 30 minutes"
---

## User Prompt

"把所有 图生视频的任务检查时间 都加到半个小时"

## Goals

- Extend polling duration for image-to-video tasks to 30 minutes across providers.

## Changes

- Increased Keling/MiniMax image-to-video polling attempts to 30 minutes at 10s intervals.
- Set Volcengine polling attempts to 30 minutes for image-to-video tasks while keeping text-to-video unchanged.

## Validation

- `pytest` (timed out in this environment; multiple failures observed during run).
- `./docker/build_prod_images.sh` (success; tag `e9fb068`).
- Chrome MCP: logged into `http://localhost:8089/login` with `geyunfei` / `Gyf@845261`, redirected to home dashboard.

## Next Steps

- Re-run `pytest` under the standard Python 3.11 environment to confirm baseline test status.

## Linked Commits

- (pending)
