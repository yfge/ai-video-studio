---
id: 2025-12-14T14-21-50Z-storyboard-video-switcher
date: 2025-12-14T14:21:50Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, video]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Add arrow controls to switch between multiple storyboard videos per frame"
---

## User Prompt

在分镜视频加一个左右 箭头 选择切换是不是比较好？

## Goals

- 让分镜卡片在有多条 `video_urls` 时可以在不同版本间快速切换。
- 保持当前播放器与封面/尾帧随选中的版本更新。

## Changes

- 为分镜页引入 `videoSelection` 状态，按 `frame_id` 存储当前视频索引。
- 解析 `video_urls/video_thumbnail_urls/video_last_frame_urls` 后，视频卡片增加左右箭头，显示当前序号 `n/total`，切换时更新播放器、封面和尾帧展示。（`ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`）

## Validation

- `cd ai-pic-frontend && npm run lint`（此前同一改动已通过；未再改动其他文件）
- Chrome：登录后在 `http://localhost:8089/episodes/10/storyboard` 页面正常，存在多版本时显示箭头并可切换。

## Next Steps

- 如需展示视频列表缩略图或下载全部版本，可再加列表 UI；当前仅支持箭头切换。

## Linked Commits

- fix(frontend): keep manual storyboard scene selection
- feat(storyboard): store video outputs as arrays
