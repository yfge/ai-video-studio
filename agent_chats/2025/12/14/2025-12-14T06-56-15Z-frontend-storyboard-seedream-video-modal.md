---
id: 2025-12-14T06-56-15Z-frontend-storyboard-seedream-video-modal
date: 2025-12-14T06:56:15Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, video, seedream]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Add Seedream image-to-video modal in storyboard management and render playable generated videos with normalized URLs."
---

## User Prompt

实现 Seedream 的图生视频：分镜管理点击视频生成弹出 modal（首帧/尾帧图组 + prompt），模型仅 Seedream 且参数对齐；任务完成上传 OSS；分镜管理展示并可播放视频。

## Goals

- 分镜管理点击“生成视频”弹出图生视频 modal，允许从首帧/尾帧候选中选择并编辑 prompt。
- modal 仅展示 Seedream 图生视频模型（通过 `model_type=image_to_video` + `seedream` 过滤）。
- 分镜帧展示已生成的视频，支持播放，并对相对路径做 URL 归一化。

## Changes

- 新增 `StoryboardVideoModal`：展示首/尾帧候选图、prompt、时长/分辨率/宽高比/水印/seed/固定摄像头等参数，并提交异步生成任务。
- 分镜页集成视频 modal，并在每个分镜卡片内展示生成的视频播放器与下载链接（含封面/尾帧链接）。
- 对 `video_url/video_thumbnail_url/video_last_frame_url` 做 `apiBase` 归一化，避免后端回传相对路径导致无法播放/打开。

## Validation

- Frontend lint: `npm run lint`
- Chrome (MCP) smoke check: 打开 `http://localhost:8089/episodes/10/storyboard`，确认关键帧预览正常且点击“生成视频”会弹出视频生成弹窗；该页面运行的前端服务疑似未更新到本次改动（弹窗仍显示旧文案/模型列表），需要在合并后重启/重新构建前端服务再复验 Seedream-only 模型筛选与参数展示。

## Next Steps

- 在重启后的前端环境中复验：弹窗应只显示 `seedream-i2v-*` 模型，并能成功提交任务后在分镜卡片里播放生成视频。

## Linked Commits

- (pending)
