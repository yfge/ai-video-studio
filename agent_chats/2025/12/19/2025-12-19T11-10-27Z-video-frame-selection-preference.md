---
id: 2025-12-19T11-10-27Z-video-frame-selection-preference
date: 2025-12-19T11:10:35Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, bugfix]
related_paths:
  - ai-pic-backend/app/services/video/video_task_utils.py
summary: "Prefer video-generation selection end frame over storyboard defaults"
---

## User Prompt

- 检查首帧/尾帧是否按分镜默认或按图生视频选择，要求以后者为准。

## Goals

- Ensure end-frame usage respects the selection made during video generation.

## Changes

- When a selection includes a start frame but no end frame, stop falling back to storyboard end frames in `resolve_frame_urls`.

## Validation

- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `04a77d1`).
- Chrome MCP: logged in and opened `http://localhost:8089/tasks`.

## Next Steps

- Submit a new video with a selected start frame and no end frame to confirm no end frame is used.

## Linked Commits

- Pending
